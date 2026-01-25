#!/bin/bash

# Скрипт автоматического деплоя Telegram-бота
# Использование: ./deploy.sh [docker|systemd]

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Функция вывода сообщений
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Проверка наличия .env файла
check_env_file() {
    if [ ! -f .env ]; then
        log_error ".env файл не найден!"
        log_info "Создайте .env файл на основе .env.example:"
        log_info "cp .env.example .env"
        log_info "И заполните необходимые переменные"
        exit 1
    fi
    log_info ".env файл найден ✓"
}

# Деплой через Docker
deploy_docker() {
    log_info "Начинаем деплой через Docker..."

    # Проверка установки Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker не установлен!"
        log_info "Установите Docker: https://docs.docker.com/get-docker/"
        exit 1
    fi

    # Проверка установки Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose не установлен!"
        log_info "Установите Docker Compose: https://docs.docker.com/compose/install/"
        exit 1
    fi

    log_info "Остановка старых контейнеров..."
    docker-compose down || true

    log_info "Сборка Docker образа..."
    docker-compose build

    log_info "Запуск контейнера..."
    docker-compose up -d

    log_info "Проверка статуса контейнера..."
    sleep 3
    docker-compose ps

    log_info "Просмотр логов (последние 20 строк):"
    docker-compose logs --tail=20

    log_info ""
    log_info "========================================="
    log_info "Деплой через Docker завершен успешно! ✓"
    log_info "========================================="
    log_info ""
    log_info "Полезные команды:"
    log_info "  Просмотр логов:      docker-compose logs -f"
    log_info "  Остановка бота:      docker-compose down"
    log_info "  Перезапуск бота:     docker-compose restart"
    log_info "  Статус контейнера:   docker-compose ps"
}

# Деплой через systemd
deploy_systemd() {
    log_info "Начинаем деплой через systemd..."

    # Проверка прав root
    if [ "$EUID" -ne 0 ]; then
        log_error "Для установки systemd service требуются права root"
        log_info "Запустите скрипт с sudo: sudo ./deploy.sh systemd"
        exit 1
    fi

    # Проверка установки Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 не установлен!"
        exit 1
    fi

    # Создание виртуального окружения если не существует
    if [ ! -d "venv" ]; then
        log_info "Создание виртуального окружения..."
        python3 -m venv venv
    fi

    # Установка зависимостей
    log_info "Установка зависимостей..."
    ./venv/bin/pip install -r requirements.txt

    # Создание директории для логов
    log_info "Создание директории для логов..."
    mkdir -p /var/log/telegram-bot
    chown $SUDO_USER:$SUDO_USER /var/log/telegram-bot

    # Копирование и настройка systemd service
    log_info "Настройка systemd service..."
    CURRENT_USER=$SUDO_USER
    CURRENT_DIR=$(pwd)

    # Замена путей в service файле
    sed -e "s|/home/ubuntu|$HOME|g" \
        -e "s|User=ubuntu|User=$CURRENT_USER|g" \
        telegram-bot.service > /tmp/telegram-bot.service

    # Копирование service файла
    cp /tmp/telegram-bot.service /etc/systemd/system/telegram-bot.service

    # Перезагрузка systemd
    log_info "Перезагрузка systemd..."
    systemctl daemon-reload

    # Включение автозапуска
    log_info "Включение автозапуска..."
    systemctl enable telegram-bot.service

    # Запуск сервиса
    log_info "Запуск сервиса..."
    systemctl restart telegram-bot.service

    # Проверка статуса
    sleep 2
    log_info "Статус сервиса:"
    systemctl status telegram-bot.service --no-pager

    log_info ""
    log_info "========================================="
    log_info "Деплой через systemd завершен успешно! ✓"
    log_info "========================================="
    log_info ""
    log_info "Полезные команды:"
    log_info "  Просмотр логов:      journalctl -u telegram-bot.service -f"
    log_info "  Остановка бота:      sudo systemctl stop telegram-bot.service"
    log_info "  Перезапуск бота:     sudo systemctl restart telegram-bot.service"
    log_info "  Статус сервиса:      sudo systemctl status telegram-bot.service"
}

# Главная функция
main() {
    log_info "====================================="
    log_info "Деплой Telegram-бота"
    log_info "====================================="
    echo ""

    # Проверка .env файла
    check_env_file

    # Определение метода деплоя
    DEPLOY_METHOD=${1:-docker}

    case $DEPLOY_METHOD in
        docker)
            deploy_docker
            ;;
        systemd)
            deploy_systemd
            ;;
        *)
            log_error "Неизвестный метод деплоя: $DEPLOY_METHOD"
            log_info "Использование: ./deploy.sh [docker|systemd]"
            exit 1
            ;;
    esac
}

# Запуск главной функции
main "$@"
