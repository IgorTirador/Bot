import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
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


async def check_subscription(user_id: int) -> bool:
    """
    Проверка подписки пользователя на канал через Telegram API.

    Args:
        user_id: ID пользователя Telegram

    Returns:
        True если пользователь подписан, False в противном случае
    """
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        # Статусы: creator, administrator, member - пользователь подписан
        # left, kicked - пользователь не подписан
        return member.status in ['creator', 'administrator', 'member']
    except Exception as e:
        logger.error(f"Ошибка при проверке подписки: {e}")
        return False


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

    # Проверяем, подписан ли уже пользователь
    is_subscribed = await check_subscription(user_id)

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

    # Проверяем подписку
    is_subscribed = await check_subscription(user_id)

    if is_subscribed:
        # Пользователь подписан - отправляем сообщение со скидкой
        await callback.message.edit_text(
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
        "/help - Показать эту справку\n\n"
        "<b>Как получить скидку:</b>\n"
        "1. Подпишитесь на наш Telegram-канал\n"
        "2. Нажмите кнопку \"✅ Проверить подписку\"\n"
        "3. Получите 50% скидку на продукт 50 мл!\n"
    )
    await message.answer(help_text, parse_mode="HTML")


async def main():
    """
    Основная функция запуска бота.
    """
    logger.info("Бот запускается...")
    try:
        # Удаление вебхука (если был установлен)
        await bot.delete_webhook(drop_pending_updates=True)
        # Запуск polling
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == '__main__':
    asyncio.run(main())
