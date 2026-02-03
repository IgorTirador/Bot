import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
from database import Database

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Получение конфигурации из .env
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')
CHANNEL_URL = os.getenv('CHANNEL_URL')
ADMIN_IDS = os.getenv('ADMIN_IDS', '').split(',')
ADMIN_IDS = [int(admin_id.strip()) for admin_id in ADMIN_IDS if admin_id.strip().isdigit()]

# Проверка наличия необходимых переменных
if not BOT_TOKEN or not CHANNEL_ID or not CHANNEL_URL:
    raise ValueError("Не установлены необходимые переменные окружения. Проверьте файл .env")

# Инициализация бота, диспетчера и базы данных
storage = MemoryStorage()
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=storage)
db = Database()

# Флаг для отслеживания проблем с конфигурацией канала
bot_config_issue = False


# States для FSM (рассылка)
class BroadcastStates(StatesGroup):
    waiting_for_message = State()


def is_admin(user_id: int) -> bool:
    """
    Проверка, является ли пользователь администратором.

    Args:
        user_id: ID пользователя

    Returns:
        True если пользователь является администратором
    """
    return user_id in ADMIN_IDS


async def save_user(message: types.Message):
    """
    Сохранение пользователя в базу данных.

    Args:
        message: Сообщение от пользователя
    """
    user = message.from_user
    db.add_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )


async def check_subscription(user_id: int) -> tuple[bool, str]:
    """
    Проверка подписки пользователя на канал через Telegram API.

    Args:
        user_id: ID пользователя Telegram

    Returns:
        Tuple[bool, str]: (статус подписки, сообщение об ошибке если есть)
    """
    global bot_config_issue

    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        # Статусы: creator, administrator, member - пользователь подписан
        # left, kicked - пользователь не подписан
        is_subscribed = member.status in ['creator', 'administrator', 'member']

        if is_subscribed:
            logger.info(f"Пользователь {user_id} подписан на канал (статус: {member.status})")
        else:
            logger.info(f"Пользователь {user_id} НЕ подписан на канал (статус: {member.status})")

        return is_subscribed, ""

    except TelegramBadRequest as e:
        error_msg = str(e)

        if "member not found" in error_msg.lower():
            # Пользователь просто не подписан на канал
            logger.info(f"Пользователь {user_id} не найден в канале (не подписан)")
            return False, ""
        elif "chat not found" in error_msg.lower():
            # Неверный CHANNEL_ID
            logger.error(f"❌ ОШИБКА КОНФИГУРАЦИИ: Канал {CHANNEL_ID} не найден! Проверьте CHANNEL_ID в .env файле")
            bot_config_issue = True
            return False, "config_error"
        else:
            logger.error(f"❌ Ошибка Telegram API при проверке подписки пользователя {user_id}: {e}")
            return False, "api_error"

    except TelegramForbiddenError as e:
        # Бот не имеет прав или не добавлен в канал
        logger.error(f"❌ ОШИБКА КОНФИГУРАЦИИ: Бот не имеет доступа к каналу {CHANNEL_ID}!")
        logger.error(f"   Убедитесь, что бот добавлен в канал как администратор с правом просмотра участников")
        bot_config_issue = True
        return False, "permission_error"

    except Exception as e:
        logger.error(f"❌ Неожиданная ошибка при проверке подписки пользователя {user_id}: {e}", exc_info=True)
        return False, "unknown_error"


def get_subscribe_keyboard() -> InlineKeyboardMarkup:
    """
    Создание клавиатуры с кнопкой подписки на канал.

    Returns:
        InlineKeyboardMarkup с кнопками подписки и проверки
    """
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Подписаться на канал", url=CHANNEL_URL)],
        [InlineKeyboardButton(text="✅ Проверить подписку", callback_data="check_subscription")]
    ])
    return keyboard


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """
    Обработчик команды /start.
    Приветствует пользователя и предлагает подписаться на канал.
    """
    user_id = message.from_user.id
    username = message.from_user.username or "Пользователь"

    logger.info(f"Команда /start от пользователя {user_id} (@{username})")

    # Сохраняем пользователя в БД
    await save_user(message)

    # Проверяем, подписан ли уже пользователь
    is_subscribed, error = await check_subscription(user_id)

    # Обновляем статус подписки в БД
    if not error:
        db.update_subscription_status(user_id, is_subscribed)

    # Если есть ошибка конфигурации
    if error in ["config_error", "permission_error"]:
        await message.answer(
            "⚠️ <b>Временные технические неполадки</b>\n\n"
            "Извините, в данный момент проверка подписки недоступна. "
            "Пожалуйста, попробуйте позже или обратитесь к администратору.\n\n"
            "Администратор: проверьте логи бота и конфигурацию канала.",
            parse_mode="HTML"
        )
        return

    if is_subscribed:
        # ============================================================
        # СООБЩЕНИЕ ДЛЯ ПОДПИСАННЫХ ПОЛЬЗОВАТЕЛЕЙ
        # ============================================================
        # Это сообщение видят пользователи, которые уже подписаны на канал
        # Здесь можно изменить:
        # - Текст приветствия
        # - Размер скидки (сейчас 20%)
        # - Описание продукции и предложений
        # ============================================================

        # Кнопки для подписанных пользователей
        # Здесь можно изменить:
        # - Текст на кнопках (text="...")
        # - Ссылки (url="...")
        # - Добавить новые кнопки, скопировав строку с InlineKeyboardButton
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎁 Получить скидку 20%", callback_data="get_discount")],  # Кнопка показывает инструкцию
            [InlineKeyboardButton(text="🎭 Получить свой Тест-драйв", url="https://forms.yandex.ru/u/697eaf7e90fa7b4317fd26bd")],  # Ссылка на форму
            [InlineKeyboardButton(text="💬 Обратиться к менеджеру", url="https://t.me/xscosmo")]  # Ссылка на менеджера
        ])

        await message.answer(
            # ТЕКСТ ПРИВЕТСТВИЯ ДЛЯ ПОДПИСАННЫХ (можно редактировать)
            "Приветствую в Xenia Cosmo🥂  Вам доступна скидка 20% на парфюм объемом от 50 мл🥳\n\n"
            "Если вы впервые, воспользуйтесь предложением \"Тест-Драйв\" - три или пять миниатюр "
            "объемом 3 мл. В наборе можно собрать разные, интересующие, ароматы. "
            "А если теряетесь в выборе и хотите поэкспериментировать, обратитесь к нам - "
            "мы сделаем персональную подборку.\n\n"
            "Возникли вопросы - обратитесь к менеджеру.",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    else:
        # ============================================================
        # СООБЩЕНИЕ ДЛЯ НЕПОДПИСАННЫХ ПОЛЬЗОВАТЕЛЕЙ
        # ============================================================
        # Это сообщение видят пользователи, которые еще НЕ подписаны на канал
        # Здесь можно изменить:
        # - Текст приглашения
        # - Размер скидки
        # - Описание преимуществ подписки
        # ============================================================

        await message.answer(
            # ТЕКСТ ПРИГЛАШЕНИЯ ДЛЯ НЕПОДПИСАННЫХ (можно редактировать)
            "Приветствую в Xenia Cosmo🥂\n\n"
            "Подпишитесь на наш Telegram-канал и получите скидку 20% на парфюм объемом от 50 мл🥳\n\n"
            "После подписки нажмите кнопку <b>\"✅ Проверить подписку\"</b>",
            reply_markup=get_subscribe_keyboard(),
            parse_mode="HTML"
        )


@dp.callback_query(F.data == "check_subscription")
async def callback_check_subscription(callback: types.CallbackQuery):
    """
    Обработчик нажатия кнопки проверки подписки.
    Проверяет статус подписки пользователя на канал.
    """
    user_id = callback.from_user.id
    username = callback.from_user.username or "Пользователь"

    logger.info(f"Проверка подписки для пользователя {user_id} (@{username})")

    # Проверяем подписку
    is_subscribed, error = await check_subscription(user_id)

    # Обновляем статус подписки в БД
    if not error:
        db.update_subscription_status(user_id, is_subscribed)

    # Если есть ошибка конфигурации
    if error in ["config_error", "permission_error"]:
        await callback.answer(
            "⚠️ Временные технические неполадки. Попробуйте позже.",
            show_alert=True
        )
        return

    if is_subscribed:
        # ============================================================
        # СООБЩЕНИЕ ПОСЛЕ УСПЕШНОЙ ПРОВЕРКИ ПОДПИСКИ
        # ============================================================
        # Это сообщение появляется после нажатия кнопки "Проверить подписку"
        # если пользователь действительно подписался
        # ============================================================

        # ТЕКСТ ПРИВЕТСТВИЯ ПОСЛЕ ПРОВЕРКИ (можно редактировать)
        welcome_text = (
            "Приветствую в Xenia Cosmo🥂  Вам доступна скидка 20% на парфюм объемом от 50 мл🥳\n\n"
            "Если вы впервые, воспользуйтесь предложением \"Тест-Драйв\" - три или пять миниатюр "
            "объемом 3 мл. В наборе можно собрать разные, интересующие, ароматы. "
            "А если теряетесь в выборе и хотите поэкспериментировать, обратитесь к нам - "
            "мы сделаем персональную подборку.\n\n"
            "Возникли вопросы - обратитесь к менеджеру."
        )

        # КНОПКИ для подписанных (можно редактировать текст и ссылки)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎁 Получить скидку 20%", callback_data="get_discount")],  # Показывает инструкцию по скидке
            [InlineKeyboardButton(text="🎭 Получить свой Тест-драйв", url="https://forms.yandex.ru/u/697eaf7e90fa7b4317fd26bd")],  # Форма Yandex
            [InlineKeyboardButton(text="💬 Обратиться к менеджеру", url="https://t.me/xscosmo")]  # Telegram менеджера
        ])

        try:
            await callback.message.edit_text(
                welcome_text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        except Exception as e:
            logger.warning(f"Не удалось отредактировать сообщение: {e}")
            # Отправляем новое сообщение
            await callback.message.answer(
                welcome_text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )

        # ВСПЛЫВАЮЩЕЕ УВЕДОМЛЕНИЕ (можно редактировать)
        await callback.answer("✅ Подписка подтверждена!", show_alert=True)
    else:
        # ============================================================
        # СООБЩЕНИЕ ЕСЛИ ПОЛЬЗОВАТЕЛЬ ЕЩЕ НЕ ПОДПИСАЛСЯ
        # ============================================================

        # ТЕКСТ ОШИБКИ (можно редактировать)
        await callback.answer(
            "❌ Вы еще не подписались на канал. Пожалуйста, подпишитесь и попробуйте снова.",
            show_alert=True
        )


@dp.callback_query(F.data == "get_discount")
async def callback_get_discount(callback: types.CallbackQuery):
    """
    Обработчик нажатия кнопки "Получить скидку 20%".
    Показывает инструкции по получению скидки.
    """
    # ============================================================
    # ИНСТРУКЦИЯ ПО ПОЛУЧЕНИЮ СКИДКИ
    # ============================================================
    # Это сообщение появляется при нажатии кнопки "Получить скидку 20%"
    # Здесь можно изменить:
    # - Размер скидки
    # - Инструкции по получению
    # - Контакт менеджера
    # - Условия скидки
    # ============================================================

    discount_text = (
        "🎁 <b>Как получить скидку 20%</b>\n\n"
        "Для получения скидки обратитесь к менеджеру @xscosmo и сообщите, "
        "что вы подписались на канал через бота.\n\n"
        "Скидка действует на парфюм объемом от 50 мл.\n\n"
        "Ждем вас! 🥂"
    )

    await callback.answer()
    await callback.message.answer(discount_text, parse_mode="HTML")


@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    """
    Обработчик команды /help.
    Выводит справочную информацию о боте.
    """
    help_text = (
        "ℹ️ <b>Справка по боту</b>\n\n"
        "<b>Команды:</b>\n"
        "/start - Начать работу с ботом\n"
        "/help - Показать эту справку\n"
        "/status - Проверить конфигурацию бота (для администраторов)\n\n"
        "<b>Как получить скидку:</b>\n"
        "1. Подпишитесь на наш Telegram-канал\n"
        "2. Нажмите кнопку \"✅ Проверить подписку\"\n"
        "3. Получите 50% скидку на продукт 50 мл!\n"
    )
    await message.answer(help_text, parse_mode="HTML")


@dp.message(Command("status"))
async def cmd_status(message: types.Message):
    """
    Обработчик команды /status.
    Проверяет конфигурацию бота и доступ к каналу.
    """
    logger.info(f"Команда /status от пользователя {message.from_user.id}")

    status_text = "🔍 <b>Статус бота</b>\n\n"

    # Проверка базовой конфигурации
    status_text += "📋 <b>Конфигурация:</b>\n"
    status_text += f"✅ BOT_TOKEN: {'установлен' if BOT_TOKEN else '❌ не установлен'}\n"
    status_text += f"✅ CHANNEL_ID: {CHANNEL_ID}\n"
    status_text += f"✅ CHANNEL_URL: {CHANNEL_URL}\n\n"

    # Проверка доступа к каналу
    status_text += "🔐 <b>Проверка доступа к каналу:</b>\n"

    try:
        # Получаем информацию о канале
        chat = await bot.get_chat(CHANNEL_ID)
        status_text += f"✅ Канал найден: {chat.title}\n"
        status_text += f"   Тип: {chat.type}\n"

        # Проверяем права бота
        try:
            bot_member = await bot.get_chat_member(CHANNEL_ID, (await bot.get_me()).id)
            status_text += f"✅ Бот в канале: {bot_member.status}\n"

            if bot_member.status in ['administrator', 'creator']:
                status_text += "✅ Бот имеет права администратора\n"
            else:
                status_text += "⚠️ Бот НЕ является администратором!\n"
                status_text += "   Добавьте бота как администратора для проверки подписки\n"

        except Exception as e:
            status_text += f"❌ Ошибка проверки прав: {e}\n"
            status_text += "   Добавьте бота в канал как администратора\n"

    except TelegramBadRequest as e:
        status_text += f"❌ Ошибка доступа к каналу: {e}\n"
        status_text += "   Проверьте CHANNEL_ID в .env файле\n"
    except Exception as e:
        status_text += f"❌ Неожиданная ошибка: {e}\n"

    status_text += "\n"
    status_text += "💡 <b>Что нужно для работы:</b>\n"
    status_text += "1. Бот должен быть добавлен в канал\n"
    status_text += "2. Бот должен быть администратором канала\n"
    status_text += "3. У бота должны быть права на просмотр участников\n"

    await message.answer(status_text, parse_mode="HTML")


# ============== АДМИН-КОМАНДЫ ==============

@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    """
    Обработчик команды /admin.
    Админ-панель с командами управления.
    """
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа к админ-панели.")
        return

    await save_user(message)

    admin_text = (
        "🔧 <b>Админ-панель</b>\n\n"
        "<b>Доступные команды:</b>\n"
        "/stats - Статистика пользователей\n"
        "/broadcast - Запустить рассылку\n"
        "/history - История рассылок\n"
        "/status - Проверка конфигурации бота\n\n"
        f"<b>Ваш ID:</b> <code>{message.from_user.id}</code>\n"
        f"<b>Администраторов:</b> {len(ADMIN_IDS)}"
    )

    await message.answer(admin_text, parse_mode="HTML")


@dp.message(Command("stats"))
async def cmd_stats(message: types.Message):
    """
    Обработчик команды /stats.
    Показывает статистику пользователей.
    """
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа к статистике.")
        return

    total, subscribed, blocked = db.get_stats()

    stats_text = (
        "📊 <b>Статистика пользователей</b>\n\n"
        f"👥 Всего пользователей: <b>{total}</b>\n"
        f"✅ Подписанных: <b>{subscribed}</b>\n"
        f"❌ Заблокировали бота: <b>{blocked}</b>\n"
        f"🎯 Активных: <b>{total - blocked}</b>\n\n"
        f"📈 Конверсия: <b>{(subscribed / total * 100):.1f}%</b> (из всех пользователей)"
        if total > 0 else "Пользователей пока нет"
    )

    await message.answer(stats_text, parse_mode="HTML")


@dp.message(Command("broadcast"))
async def cmd_broadcast(message: types.Message, state: FSMContext):
    """
    Обработчик команды /broadcast.
    Запуск рассылки сообщений всем пользователям.
    """
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа к рассылке.")
        return

    total_users = len(db.get_all_users(only_active=True))

    if total_users == 0:
        await message.answer("❌ Нет пользователей для рассылки.")
        return

    await state.set_state(BroadcastStates.waiting_for_message)

    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отменить рассылку")]],
        resize_keyboard=True
    )

    await message.answer(
        f"📢 <b>Запуск рассылки</b>\n\n"
        f"Активных пользователей: <b>{total_users}</b>\n\n"
        f"Отправьте сообщение, которое нужно разослать всем пользователям.\n"
        f"Поддерживаются: текст, фото, видео, документы.\n\n"
        f"Для отмены нажмите кнопку ниже.",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@dp.message(BroadcastStates.waiting_for_message)
async def process_broadcast_message(message: types.Message, state: FSMContext):
    """
    Обработчик сообщения для рассылки.
    Выполняет рассылку всем пользователям.
    """
    # Проверка на отмену
    if message.text == "❌ Отменить рассылку":
        await state.clear()
        await message.answer(
            "❌ Рассылка отменена.",
            reply_markup=types.ReplyKeyboardRemove()
        )
        return

    # Получаем список пользователей
    users = db.get_all_users(only_active=True)

    if not users:
        await state.clear()
        await message.answer(
            "❌ Нет пользователей для рассылки.",
            reply_markup=types.ReplyKeyboardRemove()
        )
        return

    # Создаем запись о рассылке в БД
    broadcast_id = db.create_broadcast(
        admin_id=message.from_user.id,
        message_text=message.text or message.caption or "[медиа]",
        total_users=len(users)
    )

    await state.clear()

    # Отправляем подтверждение
    status_msg = await message.answer(
        f"⏳ <b>Рассылка запущена...</b>\n\n"
        f"Всего пользователей: {len(users)}\n"
        f"Отправлено: 0\n"
        f"Ошибок: 0",
        reply_markup=types.ReplyKeyboardRemove(),
        parse_mode="HTML"
    )

    # Выполняем рассылку
    sent_count = 0
    failed_count = 0

    logger.info(f"Начало рассылки #{broadcast_id} для {len(users)} пользователей")

    for i, user_id in enumerate(users, 1):
        try:
            # Копируем сообщение пользователю
            await message.copy_to(user_id)
            sent_count += 1

            # Задержка для защиты от rate limits (30 сообщений в секунду)
            await asyncio.sleep(0.05)

        except TelegramForbiddenError:
            # Пользователь заблокировал бота
            db.mark_user_blocked(user_id)
            failed_count += 1
            logger.info(f"Пользователь {user_id} заблокировал бота")

        except Exception as e:
            failed_count += 1
            logger.error(f"Ошибка при отправке пользователю {user_id}: {e}")

        # Обновляем статус каждые 10 пользователей
        if i % 10 == 0:
            try:
                await status_msg.edit_text(
                    f"⏳ <b>Рассылка в процессе...</b>\n\n"
                    f"Всего пользователей: {len(users)}\n"
                    f"Отправлено: {sent_count}\n"
                    f"Ошибок: {failed_count}\n"
                    f"Прогресс: {i}/{len(users)} ({i/len(users)*100:.1f}%)",
                    parse_mode="HTML"
                )
            except:
                pass

    # Обновляем статистику в БД
    if broadcast_id:
        db.update_broadcast_stats(
            broadcast_id=broadcast_id,
            sent_count=sent_count,
            failed_count=failed_count,
            completed=True
        )

    # Финальное сообщение
    await status_msg.edit_text(
        f"✅ <b>Рассылка завершена!</b>\n\n"
        f"Всего пользователей: {len(users)}\n"
        f"✅ Успешно отправлено: {sent_count}\n"
        f"❌ Ошибок: {failed_count}\n"
        f"📊 Успешность: {sent_count/len(users)*100:.1f}%",
        parse_mode="HTML"
    )

    logger.info(f"Рассылка #{broadcast_id} завершена: отправлено={sent_count}, ошибок={failed_count}")


@dp.message(Command("history"))
async def cmd_history(message: types.Message):
    """
    Обработчик команды /history.
    Показывает историю рассылок.
    """
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа к истории рассылок.")
        return

    broadcasts = db.get_broadcast_history(limit=10)

    if not broadcasts:
        await message.answer("📭 История рассылок пуста.")
        return

    history_text = "📜 <b>История рассылок</b>\n\n"

    for broadcast in broadcasts:
        status = "✅" if broadcast['completed_at'] else "⏳"
        success_rate = (
            f"{broadcast['sent_count']/broadcast['total_users']*100:.1f}%"
            if broadcast['total_users'] > 0 else "0%"
        )

        history_text += (
            f"{status} <b>Рассылка #{broadcast['id']}</b>\n"
            f"   Текст: <i>{broadcast['message_text']}</i>\n"
            f"   Отправлено: {broadcast['sent_count']}/{broadcast['total_users']} ({success_rate})\n"
            f"   Дата: {broadcast['created_at'][:19]}\n\n"
        )

    await message.answer(history_text, parse_mode="HTML")


# ============== КОНЕЦ АДМИН-КОМАНД ==============


async def check_bot_config():
    """
    Проверка конфигурации бота при запуске.
    """
    logger.info("=" * 60)
    logger.info("Проверка конфигурации бота...")
    logger.info("=" * 60)

    try:
        # Получаем информацию о боте
        me = await bot.get_me()
        logger.info(f"✅ Бот успешно авторизован: @{me.username} (ID: {me.id})")

        # Проверяем доступ к каналу
        try:
            chat = await bot.get_chat(CHANNEL_ID)
            logger.info(f"✅ Канал найден: {chat.title} (ID: {chat.id}, Тип: {chat.type})")

            # Проверяем права бота в канале
            try:
                bot_member = await bot.get_chat_member(CHANNEL_ID, me.id)
                logger.info(f"✅ Бот в канале со статусом: {bot_member.status}")

                if bot_member.status in ['administrator', 'creator']:
                    logger.info("✅ Бот имеет права администратора - проверка подписки будет работать")
                else:
                    logger.warning("⚠️  ВНИМАНИЕ: Бот НЕ является администратором канала!")
                    logger.warning("   Проверка подписки НЕ будет работать!")
                    logger.warning("   Добавьте бота в канал как администратора")

            except TelegramForbiddenError:
                logger.error("❌ ОШИБКА: Бот не имеет доступа к каналу!")
                logger.error("   Добавьте бота в канал как администратора")
                return False

            except TelegramBadRequest as e:
                if "user not found" in str(e).lower():
                    logger.error("❌ ОШИБКА: Бот не найден в канале!")
                    logger.error("   Добавьте бота в канал как администратора")
                else:
                    logger.error(f"❌ ОШИБКА при проверке прав бота: {e}")
                return False

        except TelegramBadRequest as e:
            logger.error(f"❌ ОШИБКА: Канал {CHANNEL_ID} не найден!")
            logger.error(f"   Проверьте CHANNEL_ID в .env файле")
            logger.error(f"   Ошибка: {e}")
            return False

    except Exception as e:
        logger.error(f"❌ ОШИБКА при проверке конфигурации: {e}", exc_info=True)
        return False

    logger.info("=" * 60)
    logger.info("Конфигурация проверена успешно!")
    logger.info(f"URL канала: {CHANNEL_URL}")
    logger.info("=" * 60)
    return True


async def main():
    """
    Основная функция запуска бота.
    """
    logger.info("Запуск Telegram-бота для проверки подписки на канал")

    # Проверка конфигурации
    config_ok = await check_bot_config()

    if not config_ok:
        logger.error("")
        logger.error("⚠️  Бот запущен, но конфигурация неполная!")
        logger.error("⚠️  Проверка подписки может не работать!")
        logger.error("⚠️  Используйте команду /status в боте для диагностики")
        logger.error("")

    try:
        # Удаление вебхука (если был установлен)
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("🚀 Бот запущен и готов к работе!")
        logger.info("Нажмите Ctrl+C для остановки")
        logger.info("")

        # Запуск polling
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logger.info("Получен сигнал остановки...")
    finally:
        logger.info("Закрытие соединений...")
        await bot.session.close()
        logger.info("Бот остановлен")


if __name__ == '__main__':
    asyncio.run(main())
