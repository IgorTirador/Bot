# Telegram Bot - Проверка подписки на канал с QR-кодом

Telegram-бот для автоматической проверки подписки пользователей на канал с генерацией QR-кодов и UTM-метками для аналитики.

## Функционал

- ✅ Автоматическая проверка подписки на Telegram-канал через API
- 📱 Генерация QR-кодов с UTM-метками для аналитики
- 🎁 Автоматическая отправка сообщения со скидкой 50% после подтверждения подписки
- 📊 Поддержка UTM-меток для отслеживания эффективности QR-кодов

## Требования

- Python 3.8+
- Telegram Bot Token (получить у [@BotFather](https://t.me/BotFather))
- Telegram-канал с правами администратора для бота

## Установка

### 1. Клонирование репозитория

```bash
git clone <repository-url>
cd Bot
```

### 2. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 3. Настройка окружения

Скопируйте файл `.env.example` в `.env`:

```bash
cp .env.example .env
```

Отредактируйте `.env` файл и заполните необходимые данные:

```env
# Telegram Bot Configuration
BOT_TOKEN=your_bot_token_here          # Токен бота от @BotFather
BOT_USERNAME=your_bot_username         # Username бота (без @)
CHANNEL_ID=@your_channel_username      # ID или username канала (с @)
CHANNEL_URL=https://t.me/your_channel  # URL вашего канала

# UTM параметры для аналитики
UTM_SOURCE=qr_code
UTM_MEDIUM=offline
UTM_CAMPAIGN=subscription_discount
```

### 4. Настройка прав бота в канале

**ВАЖНО:** Добавьте бота в ваш Telegram-канал как администратора с правами:
- ✅ Просмотр сообщений (чтобы бот мог проверять подписку)

Как добавить бота:
1. Откройте ваш канал
2. Перейдите в настройки → Администраторы
3. Добавьте вашего бота через поиск
4. Предоставьте минимальные права (достаточно просмотра)

## Запуск

### Локальный запуск (для разработки)

```bash
python bot.py
```

Бот запустится и будет ожидать команды от пользователей.

### Генерация QR-кода

```bash
python generate_qr.py
```

QR-код будет сохранен в директории `qr_codes/bot_subscription_qr.png`

## Деплой на сервер

Проект поддерживает несколько способов деплоя на сервер.

### Автоматический деплой (рекомендуется)

Используйте скрипт автоматического деплоя:

```bash
# Деплой через Docker (рекомендуется)
./deploy.sh docker

# Деплой через systemd
sudo ./deploy.sh systemd
```

### Вариант 1: Деплой через Docker (рекомендуется)

**Преимущества:**
- Изолированная среда
- Простое обновление и откат
- Не требует настройки Python на сервере
- Автоматический перезапуск при падении

**Требования:**
- Установленный Docker
- Установленный Docker Compose

**Шаги:**

1. Установите Docker и Docker Compose на сервере:
```bash
# Установка Docker (Ubuntu/Debian)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Установка Docker Compose
sudo apt install docker-compose-plugin
```

2. Склонируйте репозиторий на сервер:
```bash
git clone <repository-url>
cd Bot
```

3. Настройте `.env` файл:
```bash
cp .env.example .env
nano .env  # Заполните необходимые данные
```

4. Запустите бота:
```bash
docker-compose up -d
```

**Полезные команды:**

```bash
# Просмотр логов
docker-compose logs -f

# Остановка бота
docker-compose down

# Перезапуск бота
docker-compose restart

# Обновление бота
git pull
docker-compose down
docker-compose build
docker-compose up -d

# Проверка статуса
docker-compose ps
```

### Вариант 2: Деплой через systemd (Linux)

**Преимущества:**
- Нативная интеграция с системой
- Автозапуск при перезагрузке сервера
- Управление через systemctl

**Требования:**
- Linux сервер с systemd
- Python 3.8+

**Шаги:**

1. Склонируйте репозиторий:
```bash
git clone <repository-url>
cd Bot
```

2. Создайте виртуальное окружение и установите зависимости:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. Настройте `.env` файл:
```bash
cp .env.example .env
nano .env  # Заполните необходимые данные
```

4. Установите systemd service:
```bash
# Отредактируйте telegram-bot.service, укажите правильные пути
# Замените /home/ubuntu на путь к вашей директории
# Замените User=ubuntu на вашего пользователя

sudo cp telegram-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable telegram-bot.service
sudo systemctl start telegram-bot.service
```

**Полезные команды:**

```bash
# Просмотр статуса
sudo systemctl status telegram-bot.service

# Просмотр логов
sudo journalctl -u telegram-bot.service -f

# Перезапуск бота
sudo systemctl restart telegram-bot.service

# Остановка бота
sudo systemctl stop telegram-bot.service

# Отключение автозапуска
sudo systemctl disable telegram-bot.service
```

### Вариант 3: Деплой на VPS (ручной способ)

1. Подключитесь к серверу:
```bash
ssh user@your-server-ip
```

2. Установите необходимые пакеты:
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv git
```

3. Склонируйте репозиторий:
```bash
git clone <repository-url>
cd Bot
```

4. Создайте виртуальное окружение:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

5. Настройте `.env`:
```bash
cp .env.example .env
nano .env
```

6. Запустите бота в фоновом режиме:
```bash
nohup python bot.py > bot.log 2>&1 &
```

### Вариант 4: Деплой на облачные платформы

#### Railway.app

1. Создайте аккаунт на [Railway.app](https://railway.app/)
2. Подключите GitHub репозиторий
3. Добавьте переменные окружения из `.env`
4. Railway автоматически обнаружит Dockerfile и задеплоит бота

#### Heroku

1. Создайте `Procfile`:
```
worker: python bot.py
```

2. Деплой:
```bash
heroku create your-bot-name
heroku config:set BOT_TOKEN=your_token
heroku config:set CHANNEL_ID=@your_channel
heroku config:set CHANNEL_URL=https://t.me/your_channel
heroku config:set BOT_USERNAME=your_bot_username
git push heroku main
```

#### DigitalOcean App Platform

1. Подключите GitHub репозиторий
2. Выберите Docker как метод деплоя
3. Добавьте переменные окружения
4. Запустите деплой

### Рекомендации по безопасности при деплое

- ✅ Используйте `.env` файл для хранения секретов (никогда не коммитьте его)
- ✅ Ограничьте доступ к серверу (firewall, SSH ключи)
- ✅ Регулярно обновляйте зависимости
- ✅ Мониторьте логи на наличие ошибок
- ✅ Настройте автоматические бэкапы
- ✅ Используйте HTTPS для всех внешних запросов

## Использование

### Для пользователей

1. Сканируйте QR-код или перейдите по ссылке в бот
2. Нажмите кнопку "📢 Подписаться на канал"
3. Подпишитесь на канал
4. Вернитесь в бот и нажмите "✅ Проверить подписку"
5. Получите сообщение со скидкой 50%

### Команды бота

- `/start` - Начать работу с ботом
- `/help` - Справка по использованию

## Структура проекта

```
Bot/
├── bot.py                    # Основной файл бота
├── generate_qr.py            # Генератор QR-кодов
├── requirements.txt          # Зависимости Python
├── .env.example             # Пример конфигурации
├── .env                     # Конфигурация (не в git)
├── .gitignore               # Игнорируемые файлы
├── Dockerfile               # Docker образ для деплоя
├── docker-compose.yml       # Docker Compose конфигурация
├── telegram-bot.service     # systemd service файл
├── deploy.sh                # Скрипт автоматического деплоя
├── qr_codes/                # Директория для QR-кодов
│   └── .gitkeep
└── README.md                # Документация
```

## Технические детали

### Проверка подписки

Бот использует метод `getChatMember` из Telegram Bot API для проверки статуса пользователя в канале:

```python
async def check_subscription(user_id: int) -> bool:
    member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
    return member.status in ['creator', 'administrator', 'member']
```

Возможные статусы:
- `creator` - создатель канала
- `administrator` - администратор
- `member` - участник (подписан)
- `left` - покинул канал
- `kicked` - исключен

### UTM-метки

QR-код содержит параметр `start`, который позволяет отслеживать источник перехода:

```
https://t.me/your_bot?start=qr_code_offline
```

Вы можете изменить UTM-параметры в `.env` файле для различных кампаний.

## Безопасность

- ⚠️ **Никогда не публикуйте файл `.env` в репозитории**
- ⚠️ **Храните BOT_TOKEN в секрете**
- ⚠️ **Не делитесь токеном бота с третьими лицами**

## Решение проблем

### Бот не может проверить подписку

**Ошибка:** `Can't get chat member`

**Решение:**
1. Убедитесь, что бот добавлен в канал как администратор
2. Проверьте, что `CHANNEL_ID` в `.env` указан верно (должен начинаться с @ или быть числовым ID)

### QR-код не генерируется

**Ошибка:** `ModuleNotFoundError: No module named 'PIL'`

**Решение:**
```bash
pip install --upgrade qrcode[pil]
```

### Бот не отвечает на команды

**Решение:**
1. Проверьте, что бот запущен (`python bot.py`)
2. Убедитесь, что `BOT_TOKEN` в `.env` корректный
3. Проверьте логи на наличие ошибок

## Поддержка

При возникновении проблем:
1. Проверьте логи бота
2. Убедитесь, что все переменные в `.env` заполнены корректно
3. Проверьте права бота в канале

## Лицензия

MIT License

## Автор

Создано с использованием:
- [aiogram](https://github.com/aiogram/aiogram) - фреймворк для Telegram Bot API
- [qrcode](https://github.com/lincolnloop/python-qrcode) - генератор QR-кодов
