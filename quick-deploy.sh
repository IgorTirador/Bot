#!/bin/bash

# Быстрый деплой на VPS
# Использование: запустите этот скрипт на вашем VPS сервере

set -e

echo "============================================"
echo "  Быстрый деплой Telegram-бота на VPS"
echo "============================================"
echo ""

# Проверка, что скрипт запущен на сервере, а не локально
if [ ! -f "bot.py" ]; then
    echo "❌ Ошибка: файл bot.py не найден!"
    echo "Этот скрипт должен быть запущен в директории Bot/"
    exit 1
fi

# Проверка .env файла
if [ ! -f ".env" ]; then
    echo "⚠️  .env файл не найден!"
    echo "Создаем .env из примера..."
    cp .env.example .env
    echo ""
    echo "✏️  Пожалуйста, отредактируйте .env файл:"
    echo "   nano .env"
    echo ""
    echo "Заполните следующие параметры:"
    echo "  - BOT_TOKEN (получите у @BotFather)"
    echo "  - BOT_USERNAME (username вашего бота)"
    echo "  - CHANNEL_ID (ID или @username канала)"
    echo "  - CHANNEL_URL (ссылка на канал)"
    echo ""
    read -p "Нажмите Enter после редактирования .env файла..."
fi

echo "✅ .env файл найден"

# Проверка наличия Docker
if command -v docker &> /dev/null && command -v docker-compose &> /dev/null; then
    echo ""
    echo "🐳 Docker обнаружен!"
    echo "Выберите метод деплоя:"
    echo "  1) Docker (рекомендуется)"
    echo "  2) systemd"
    echo "  3) Простой запуск в фоне"
    read -p "Ваш выбор (1-3): " choice
else
    echo ""
    echo "Docker не установлен."
    echo "Выберите метод деплоя:"
    echo "  1) Установить Docker и использовать его (рекомендуется)"
    echo "  2) systemd"
    echo "  3) Простой запуск в фоне"
    read -p "Ваш выбор (1-3): " choice
fi

case $choice in
    1)
        # Docker деплой
        if ! command -v docker &> /dev/null; then
            echo ""
            echo "📦 Установка Docker..."
            curl -fsSL https://get.docker.com -o get-docker.sh
            sudo sh get-docker.sh
            sudo usermod -aG docker $USER

            echo "📦 Установка Docker Compose..."
            sudo apt-get update
            sudo apt-get install -y docker-compose-plugin
        fi

        echo ""
        echo "🚀 Запуск через Docker..."
        sudo docker-compose down 2>/dev/null || true
        sudo docker-compose up -d --build

        echo ""
        echo "✅ Бот запущен через Docker!"
        echo ""
        echo "Полезные команды:"
        echo "  Логи:        sudo docker-compose logs -f"
        echo "  Остановка:   sudo docker-compose down"
        echo "  Перезапуск:  sudo docker-compose restart"
        echo "  Статус:      sudo docker-compose ps"

        echo ""
        echo "Просмотр логов..."
        sudo docker-compose logs --tail=50
        ;;

    2)
        # systemd деплой
        echo ""
        echo "⚙️  Деплой через systemd..."

        # Установка Python если нужно
        if ! command -v python3 &> /dev/null; then
            echo "📦 Установка Python..."
            sudo apt-get update
            sudo apt-get install -y python3 python3-pip python3-venv
        fi

        # Создание виртуального окружения
        if [ ! -d "venv" ]; then
            echo "📦 Создание виртуального окружения..."
            python3 -m venv venv
        fi

        echo "📦 Установка зависимостей..."
        source venv/bin/activate
        pip install -q -r requirements.txt

        # Получение текущего пользователя и директории
        CURRENT_USER=$(whoami)
        CURRENT_DIR=$(pwd)

        # Создание директории для логов
        echo "📁 Создание директории для логов..."
        sudo mkdir -p /var/log/telegram-bot
        sudo chown $CURRENT_USER:$CURRENT_USER /var/log/telegram-bot

        # Создание service файла
        echo "⚙️  Настройка systemd service..."
        cat > /tmp/telegram-bot.service <<EOF
[Unit]
Description=Telegram Subscription Bot
After=network.target

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$CURRENT_DIR
Environment="PATH=$CURRENT_DIR/venv/bin"
ExecStart=$CURRENT_DIR/venv/bin/python $CURRENT_DIR/bot.py
Restart=always
RestartSec=10

StandardOutput=append:/var/log/telegram-bot/bot.log
StandardError=append:/var/log/telegram-bot/error.log

NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

        sudo cp /tmp/telegram-bot.service /etc/systemd/system/
        sudo systemctl daemon-reload
        sudo systemctl enable telegram-bot.service
        sudo systemctl restart telegram-bot.service

        sleep 2

        echo ""
        echo "✅ Бот запущен через systemd!"
        echo ""
        echo "Полезные команды:"
        echo "  Статус:      sudo systemctl status telegram-bot.service"
        echo "  Логи:        sudo journalctl -u telegram-bot.service -f"
        echo "  Перезапуск:  sudo systemctl restart telegram-bot.service"
        echo "  Остановка:   sudo systemctl stop telegram-bot.service"

        echo ""
        echo "Проверка статуса..."
        sudo systemctl status telegram-bot.service --no-pager
        ;;

    3)
        # Простой запуск
        echo ""
        echo "🔧 Простой запуск в фоне..."

        # Установка Python если нужно
        if ! command -v python3 &> /dev/null; then
            echo "📦 Установка Python..."
            sudo apt-get update
            sudo apt-get install -y python3 python3-pip python3-venv
        fi

        # Создание виртуального окружения
        if [ ! -d "venv" ]; then
            echo "📦 Создание виртуального окружения..."
            python3 -m venv venv
        fi

        echo "📦 Установка зависимостей..."
        source venv/bin/activate
        pip install -q -r requirements.txt

        # Остановка старого процесса если есть
        pkill -f "python.*bot.py" || true

        # Запуск в фоне
        echo "🚀 Запуск бота..."
        nohup python bot.py > bot.log 2>&1 &
        BOT_PID=$!

        sleep 2

        if ps -p $BOT_PID > /dev/null; then
            echo ""
            echo "✅ Бот запущен! PID: $BOT_PID"
            echo ""
            echo "Полезные команды:"
            echo "  Логи:        tail -f bot.log"
            echo "  Остановка:   pkill -f 'python.*bot.py'"
            echo "  Процесс:     ps aux | grep bot.py"

            echo ""
            echo "Последние строки лога:"
            tail -20 bot.log
        else
            echo ""
            echo "❌ Ошибка запуска бота!"
            echo "Проверьте логи: cat bot.log"
        fi
        ;;

    *)
        echo "❌ Неверный выбор"
        exit 1
        ;;
esac

echo ""
echo "============================================"
echo "  ✅ Деплой завершен!"
echo "============================================"
echo ""
echo "⚠️  ВАЖНО: Не забудьте добавить бота в канал как администратора!"
echo ""
