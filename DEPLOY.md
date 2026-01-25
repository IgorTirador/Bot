# Руководство по деплою Telegram-бота

Это руководство содержит подробные инструкции по деплою бота на различные платформы.

## Содержание

- [Автоматический деплой](#автоматический-деплой)
- [Docker](#docker)
- [systemd (Linux)](#systemd-linux)
- [VPS (Ubuntu/Debian)](#vps-ubuntudebian)
- [Облачные платформы](#облачные-платформы)
  - [Railway.app](#railwayapp)
  - [Heroku](#heroku)
  - [DigitalOcean](#digitalocean)
  - [AWS EC2](#aws-ec2)
- [Мониторинг и обслуживание](#мониторинг-и-обслуживание)

---

## Автоматический деплой

Самый простой способ деплоя - использовать встроенный скрипт `deploy.sh`:

### Docker деплой
```bash
./deploy.sh docker
```

### systemd деплой
```bash
sudo ./deploy.sh systemd
```

Скрипт автоматически:
- Проверит наличие .env файла
- Установит зависимости
- Настроит сервис
- Запустит бота
- Покажет статус и полезные команды

---

## Docker

### Предварительные требования

- Docker 20.10+
- Docker Compose 2.0+

### Установка Docker

**Ubuntu/Debian:**
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
newgrp docker
```

**CentOS/RHEL:**
```bash
sudo yum install -y yum-utils
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
sudo yum install docker-ce docker-ce-cli containerd.io
sudo systemctl start docker
sudo systemctl enable docker
```

### Деплой

1. **Клонирование репозитория:**
```bash
git clone <repository-url>
cd Bot
```

2. **Настройка окружения:**
```bash
cp .env.example .env
nano .env
```

Заполните следующие переменные:
```env
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
BOT_USERNAME=your_bot_username
CHANNEL_ID=@your_channel
CHANNEL_URL=https://t.me/your_channel
UTM_SOURCE=qr_code
UTM_MEDIUM=offline
UTM_CAMPAIGN=subscription_discount
```

3. **Сборка и запуск:**
```bash
docker-compose up -d
```

### Управление контейнером

```bash
# Просмотр логов (в реальном времени)
docker-compose logs -f

# Просмотр последних 100 строк логов
docker-compose logs --tail=100

# Остановка бота
docker-compose down

# Перезапуск бота
docker-compose restart

# Проверка статуса
docker-compose ps

# Пересборка после изменений в коде
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Обновление бота

```bash
git pull origin main
docker-compose down
docker-compose build
docker-compose up -d
```

### Решение проблем

**Проблема:** Контейнер постоянно перезапускается

**Решение:**
```bash
# Просмотр логов для диагностики
docker-compose logs

# Проверка .env файла
cat .env

# Проверка, что бот добавлен в канал как администратор
```

**Проблема:** Нет доступа к Docker

**Решение:**
```bash
sudo usermod -aG docker $USER
newgrp docker
```

---

## systemd (Linux)

### Предварительные требования

- Linux с systemd
- Python 3.8+
- pip
- git

### Установка зависимостей

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv git
```

**CentOS/RHEL:**
```bash
sudo yum install python3 python3-pip git
```

### Деплой

1. **Клонирование репозитория:**
```bash
cd /home/$USER
git clone <repository-url>
cd Bot
```

2. **Создание виртуального окружения:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. **Настройка .env:**
```bash
cp .env.example .env
nano .env  # Заполните данные
```

4. **Редактирование service файла:**
```bash
nano telegram-bot.service
```

Замените следующие параметры:
- `/home/ubuntu` → путь к вашей директории (например, `/home/youruser`)
- `User=ubuntu` → ваш пользователь (например, `User=youruser`)

5. **Установка service:**
```bash
# Создание директории для логов
sudo mkdir -p /var/log/telegram-bot
sudo chown $USER:$USER /var/log/telegram-bot

# Копирование service файла
sudo cp telegram-bot.service /etc/systemd/system/

# Перезагрузка systemd
sudo systemctl daemon-reload

# Включение автозапуска
sudo systemctl enable telegram-bot.service

# Запуск сервиса
sudo systemctl start telegram-bot.service
```

6. **Проверка статуса:**
```bash
sudo systemctl status telegram-bot.service
```

### Управление сервисом

```bash
# Запуск
sudo systemctl start telegram-bot.service

# Остановка
sudo systemctl stop telegram-bot.service

# Перезапуск
sudo systemctl restart telegram-bot.service

# Просмотр статуса
sudo systemctl status telegram-bot.service

# Просмотр логов (в реальном времени)
sudo journalctl -u telegram-bot.service -f

# Просмотр последних 100 строк логов
sudo journalctl -u telegram-bot.service -n 100

# Просмотр логов за сегодня
sudo journalctl -u telegram-bot.service --since today

# Отключение автозапуска
sudo systemctl disable telegram-bot.service
```

### Обновление бота

```bash
cd /home/$USER/Bot
git pull origin main
sudo systemctl restart telegram-bot.service
sudo systemctl status telegram-bot.service
```

---

## VPS (Ubuntu/Debian)

Ручной способ деплоя на VPS без Docker и systemd.

### 1. Подключение к серверу

```bash
ssh user@your-server-ip
```

### 2. Установка зависимостей

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install python3 python3-pip python3-venv git screen -y
```

### 3. Клонирование репозитория

```bash
cd ~
git clone <repository-url>
cd Bot
```

### 4. Настройка окружения

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 5. Настройка .env

```bash
cp .env.example .env
nano .env  # Заполните данные
```

### 6. Запуск в screen (для фонового режима)

```bash
# Создание screen сессии
screen -S telegram-bot

# Активация виртуального окружения
source venv/bin/activate

# Запуск бота
python bot.py

# Отключение от screen: Ctrl+A, затем D
```

### 7. Управление screen сессией

```bash
# Список активных сессий
screen -ls

# Подключение к сессии
screen -r telegram-bot

# Завершение сессии (внутри screen)
Ctrl+C, затем exit

# Удаление отключенной сессии
screen -X -S telegram-bot quit
```

### Альтернатива: запуск с nohup

```bash
# Запуск в фоновом режиме
nohup python bot.py > bot.log 2>&1 &

# Просмотр логов
tail -f bot.log

# Остановка бота
ps aux | grep bot.py
kill <PID>
```

---

## Облачные платформы

### Railway.app

**Преимущества:**
- Бесплатный тариф (500 часов в месяц)
- Автоматический деплой из GitHub
- Простая настройка

**Шаги:**

1. Зарегистрируйтесь на [Railway.app](https://railway.app/)

2. Создайте новый проект → Deploy from GitHub

3. Выберите ваш репозиторий

4. Добавьте переменные окружения:
   - `BOT_TOKEN`
   - `BOT_USERNAME`
   - `CHANNEL_ID`
   - `CHANNEL_URL`
   - `UTM_SOURCE`
   - `UTM_MEDIUM`
   - `UTM_CAMPAIGN`

5. Railway автоматически обнаружит Dockerfile и запустит деплой

6. Проверьте логи в разделе "Deployments"

### Heroku

**Шаги:**

1. Создайте `Procfile` в корне проекта:
```
worker: python bot.py
```

2. Установите Heroku CLI:
```bash
curl https://cli-assets.heroku.com/install.sh | sh
```

3. Логин и создание приложения:
```bash
heroku login
heroku create your-bot-name
```

4. Добавьте переменные окружения:
```bash
heroku config:set BOT_TOKEN=your_token
heroku config:set BOT_USERNAME=your_bot_username
heroku config:set CHANNEL_ID=@your_channel
heroku config:set CHANNEL_URL=https://t.me/your_channel
heroku config:set UTM_SOURCE=qr_code
heroku config:set UTM_MEDIUM=offline
heroku config:set UTM_CAMPAIGN=subscription_discount
```

5. Деплой:
```bash
git push heroku main
```

6. Включите worker dyno:
```bash
heroku ps:scale worker=1
```

7. Просмотр логов:
```bash
heroku logs --tail
```

### DigitalOcean

**App Platform:**

1. Создайте аккаунт на [DigitalOcean](https://www.digitalocean.com/)

2. Перейдите в App Platform → Create App

3. Подключите GitHub репозиторий

4. Выберите:
   - Environment: Docker
   - Type: Worker

5. Добавьте переменные окружения

6. Выберите план (Basic - $5/месяц)

7. Запустите деплой

**Droplet (VPS):**

См. раздел [VPS (Ubuntu/Debian)](#vps-ubuntudebian)

### AWS EC2

1. **Создание EC2 инстанса:**
   - Выберите Ubuntu Server 22.04 LTS
   - t2.micro (бесплатный tier)
   - Настройте Security Group (откройте SSH)

2. **Подключение:**
```bash
ssh -i your-key.pem ubuntu@ec2-instance-ip
```

3. **Следуйте инструкциям из раздела VPS**

4. **Опционально: настройка автозапуска через systemd**

См. раздел [systemd (Linux)](#systemd-linux)

---

## Мониторинг и обслуживание

### Проверка состояния бота

**Docker:**
```bash
docker-compose ps
docker-compose logs --tail=50
```

**systemd:**
```bash
sudo systemctl status telegram-bot.service
sudo journalctl -u telegram-bot.service --since "1 hour ago"
```

### Регулярное обслуживание

**Обновление зависимостей:**
```bash
pip install --upgrade -r requirements.txt
```

**Очистка логов (Docker):**
```bash
docker-compose down
docker system prune -a
docker-compose up -d
```

**Ротация логов (systemd):**
```bash
# Логи автоматически ротируются journald
# Настройка максимального размера в /etc/systemd/journald.conf
sudo nano /etc/systemd/journald.conf
# SystemMaxUse=500M
```

### Мониторинг ресурсов

**Docker:**
```bash
docker stats telegram_subscription_bot
```

**systemd:**
```bash
# CPU и память
top
htop

# Специфично для процесса
ps aux | grep bot.py
```

### Backup

**Важные файлы для резервного копирования:**
- `.env` - конфигурация
- `qr_codes/` - сгенерированные QR-коды

```bash
# Создание backup
tar -czf backup-$(date +%Y%m%d).tar.gz .env qr_codes/

# Восстановление
tar -xzf backup-20260125.tar.gz
```

### Оповещения

Рекомендуется настроить мониторинг и оповещения:

- **UptimeRobot** - проверка доступности
- **Sentry** - отслеживание ошибок
- **Grafana + Prometheus** - мониторинг метрик
- **CloudWatch** (для AWS) - логи и метрики

### Автоматические обновления

**GitHub Actions + Webhook:**

Создайте `.github/workflows/deploy.yml` для автоматического деплоя при push в main.

---

## Решение проблем

### Бот не запускается

1. Проверьте .env файл
2. Проверьте логи
3. Убедитесь, что бот добавлен в канал
4. Проверьте токен бота

### Бот не проверяет подписку

1. Убедитесь, что бот - администратор канала
2. Проверьте CHANNEL_ID (должен начинаться с @)
3. Проверьте права бота в канале

### Высокое использование памяти

1. Перезапустите бота
2. Проверьте логи на утечки памяти
3. Обновите зависимости

---

## Безопасность

### Рекомендации:

- ✅ Используйте SSH ключи вместо паролей
- ✅ Настройте firewall (ufw, iptables)
- ✅ Регулярно обновляйте систему
- ✅ Используйте .env для секретов
- ✅ Не публикуйте токены в git
- ✅ Ограничьте права бота в канале
- ✅ Используйте HTTPS для webhook (если планируете)
- ✅ Настройте автоматические backup

### Настройка firewall (ufw)

```bash
# Установка ufw
sudo apt install ufw

# Разрешить SSH
sudo ufw allow ssh

# Включить firewall
sudo ufw enable

# Проверка статуса
sudo ufw status
```

---

## Поддержка

При возникновении проблем:

1. Проверьте логи бота
2. Убедитесь в корректности .env
3. Проверьте документацию Telegram Bot API
4. Создайте issue в GitHub

---

**Удачного деплоя!** 🚀
