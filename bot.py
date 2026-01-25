import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from dotenv import load_dotenv

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

# Проверка наличия необходимых переменных
if not BOT_TOKEN or not CHANNEL_ID or not CHANNEL_URL:
    raise ValueError("Не установлены необходимые переменные окружения. Проверьте файл .env")

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Флаг для отслеживания проблем с конфигурацией канала
bot_config_issue = False


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

    # Проверяем, подписан ли уже пользователь
    is_subscribed, error = await check_subscription(user_id)

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
        # Пользователь уже подписан - отправляем сообщение со скидкой
        await message.answer(
            "🎉 <b>Вы уже подписаны на наш канал!</b>\n\n"
            "Спасибо за подписку! 🎉 Вы получаете <b>50% скидку</b> на продукт объемом 50 мл "
            "(полноформатная упаковка)!\n\n"
            "Для получения скидки обратитесь к нашему менеджеру.",
            parse_mode="HTML"
        )
    else:
        # Пользователь не подписан - предлагаем подписаться
        await message.answer(
            "👋 <b>Добро пожаловать!</b>\n\n"
            "Подпишитесь на наш Telegram-канал и получите <b>50% скидку</b> "
            "на продукт объемом 50 мл (полноформатная упаковка)!\n\n"
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

    # Если есть ошибка конфигурации
    if error in ["config_error", "permission_error"]:
        await callback.answer(
            "⚠️ Временные технические неполадки. Попробуйте позже.",
            show_alert=True
        )
        return

    if is_subscribed:
        # Пользователь подписан - отправляем сообщение со скидкой
        try:
            await callback.message.edit_text(
                "🎉 <b>Спасибо за подписку!</b>\n\n"
                "Вы получаете <b>50% скидку</b> на продукт объемом 50 мл "
                "(полноформатная упаковка)!\n\n"
                "Для получения скидки обратитесь к нашему менеджеру.",
                parse_mode="HTML"
            )
        except Exception as e:
            logger.warning(f"Не удалось отредактировать сообщение: {e}")
            # Отправляем новое сообщение
            await callback.message.answer(
                "🎉 <b>Спасибо за подписку!</b>\n\n"
                "Вы получаете <b>50% скидку</b> на продукт объемом 50 мл "
                "(полноформатная упаковка)!\n\n"
                "Для получения скидки обратитесь к нашему менеджеру.",
                parse_mode="HTML"
            )

        await callback.answer("✅ Подписка подтверждена!", show_alert=True)
    else:
        # Пользователь не подписан
        await callback.answer(
            "❌ Вы еще не подписались на канал. Пожалуйста, подпишитесь и попробуйте снова.",
            show_alert=True
        )


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
