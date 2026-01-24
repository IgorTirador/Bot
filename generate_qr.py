"""
Генератор QR-кодов для Telegram-бота с UTM-метками.

Этот скрипт создает QR-код, который направляет пользователей в Telegram-бот
с добавлением UTM-меток для аналитики.
"""

import os
import qrcode
from dotenv import load_dotenv
from urllib.parse import urlencode

# Загрузка переменных окружения
load_dotenv()


def generate_bot_url_with_utm(bot_username: str, utm_params: dict = None) -> str:
    """
    Генерирует URL бота с UTM-метками.

    Args:
        bot_username: username бота (без @)
        utm_params: словарь с UTM-параметрами (source, medium, campaign и т.д.)

    Returns:
        Полный URL с UTM-метками
    """
    # Базовый URL бота
    base_url = f"https://t.me/{bot_username}"

    # UTM-параметры по умолчанию из .env или переданные
    if utm_params is None:
        utm_params = {
            'utm_source': os.getenv('UTM_SOURCE', 'qr_code'),
            'utm_medium': os.getenv('UTM_MEDIUM', 'offline'),
            'utm_campaign': os.getenv('UTM_CAMPAIGN', 'subscription_discount')
        }

    # Добавляем параметр start для Telegram (это позволяет отслеживать источник)
    # В Telegram боте можно получить этот параметр через /start command
    start_param = f"{utm_params['utm_source']}_{utm_params['utm_medium']}"

    # Формируем URL с параметром start
    url_with_start = f"{base_url}?start={start_param}"

    return url_with_start


def generate_qr_code(url: str, output_path: str = "qr_codes/bot_qr_code.png",
                     box_size: int = 10, border: int = 4) -> str:
    """
    Генерирует QR-код для указанного URL.

    Args:
        url: URL для кодирования в QR-код
        output_path: путь для сохранения QR-кода
        box_size: размер каждого блока QR-кода (в пикселях)
        border: толщина рамки (в блоках)

    Returns:
        Путь к созданному QR-коду
    """
    # Создание директории для QR-кодов, если её нет
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Создание QR-кода
    qr = qrcode.QRCode(
        version=1,  # Размер QR-кода (1 - самый маленький)
        error_correction=qrcode.constants.ERROR_CORRECT_L,  # Уровень коррекции ошибок
        box_size=box_size,
        border=border,
    )

    qr.add_data(url)
    qr.make(fit=True)

    # Создание изображения
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(output_path)

    print(f"✅ QR-код успешно создан: {output_path}")
    print(f"🔗 URL: {url}")

    return output_path


def main():
    """
    Основная функция для генерации QR-кодов.
    """
    # Получение username бота из переменных окружения
    bot_username = os.getenv('BOT_USERNAME', 'your_bot_username')

    if bot_username == 'your_bot_username':
        print("⚠️  Предупреждение: BOT_USERNAME не установлен в .env файле")
        print("Пожалуйста, добавьте BOT_USERNAME=ваш_бот_username в .env")
        bot_username = input("Введите username вашего бота (без @): ")

    # Генерация URL с UTM-метками
    bot_url = generate_bot_url_with_utm(bot_username)

    # Генерация QR-кода
    qr_path = generate_qr_code(
        url=bot_url,
        output_path="qr_codes/bot_subscription_qr.png",
        box_size=10,
        border=4
    )

    print(f"\n📱 QR-код готов к использованию!")
    print(f"📍 Файл сохранен: {qr_path}")
    print(f"\n💡 Инструкции:")
    print(f"   1. Распечатайте QR-код или разместите его в цифровом виде")
    print(f"   2. При сканировании пользователи будут перенаправлены в ваш Telegram-бот")
    print(f"   3. UTM-метки помогут отследить эффективность QR-кода в аналитике")


if __name__ == '__main__':
    main()
