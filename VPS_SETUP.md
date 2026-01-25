# Инструкция по деплою на VPS 185.130.115.32

Это пошаговое руководство для деплоя бота на ваш VPS сервер.

## Быстрый старт (5 минут)

### Шаг 1: Подключитесь к серверу

```bash
ssh root@185.130.115.32
# или
ssh your_user@185.130.115.32
```

### Шаг 2: Установите git (если не установлен)

```bash
sudo apt update
sudo apt install -y git
```

### Шаг 3: Склонируйте репозиторий

```bash
cd ~
git clone https://github.com/IgorTirador/Bot.git
cd Bot
```

### Шаг 4: Настройте .env файл

```bash
cp .env.example .env
nano .env
```

**Заполните следующие данные:**

```env
BOT_TOKEN=ваш_токен_от_BotFather
BOT_USERNAME=username_вашего_бота
CHANNEL_ID=@ваш_канал
CHANNEL_URL=https://t.me/ваш_канал

UTM_SOURCE=qr_code
UTM_MEDIUM=offline
UTM_CAMPAIGN=subscription_discount
```

Сохраните файл: `Ctrl+O`, `Enter`, `Ctrl+X`

### Шаг 5: Запустите автоматический деплой

```bash
chmod +x quick-deploy.sh
./quick-deploy.sh
```

Скрипт автоматически:
- Проверит наличие Docker
- Предложит выбрать метод деплоя (Docker/systemd/фоновый режим)
- Установит необходимые зависимости
- Запустит бота
- Покажет логи

**Готово!** 🎉

---

## Альтернативные методы деплоя

### Метод 1: Docker (рекомендуется)

**Преимущества:**
- ✅ Изолированная среда
- ✅ Простое обновление
- ✅ Автоматический перезапуск
- ✅ Не засоряет систему

**Команды:**

```bash
# Подключение к серверу
ssh root@185.130.115.32

# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Установка Docker Compose
sudo apt install -y docker-compose-plugin

# Клонирование репозитория
cd ~
git clone https://github.com/IgorTirador/Bot.git
cd Bot

# Настройка .env
cp .env.example .env
nano .env  # Заполните данные

# Запуск
sudo docker-compose up -d

# Проверка логов
sudo docker-compose logs -f
```

**Управление:**

```bash
# Просмотр логов
sudo docker-compose logs -f

# Остановка
sudo docker-compose down

# Перезапуск
sudo docker-compose restart

# Обновление бота
cd ~/Bot
git pull
sudo docker-compose down
sudo docker-compose build
sudo docker-compose up -d

# Статус
sudo docker-compose ps
```

### Метод 2: systemd (Linux native)

**Преимущества:**
- ✅ Нативная интеграция с Linux
- ✅ Автозапуск при перезагрузке
- ✅ Централизованные логи

**Команды:**

```bash
# Подключение к серверу
ssh root@185.130.115.32

# Установка зависимостей
sudo apt update
sudo apt install -y python3 python3-pip python3-venv git

# Клонирование репозитория
cd ~
git clone https://github.com/IgorTirador/Bot.git
cd Bot

# Создание виртуального окружения
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Настройка .env
cp .env.example .env
nano .env  # Заполните данные

# Автоматический деплой через systemd
chmod +x deploy.sh
sudo ./deploy.sh systemd
```

**Управление:**

```bash
# Статус
sudo systemctl status telegram-bot.service

# Логи
sudo journalctl -u telegram-bot.service -f

# Перезапуск
sudo systemctl restart telegram-bot.service

# Остановка
sudo systemctl stop telegram-bot.service

# Отключение автозапуска
sudo systemctl disable telegram-bot.service
```

### Метод 3: Простой запуск в фоне

**Для быстрого тестирования:**

```bash
# Подключение
ssh root@185.130.115.32

# Установка зависимостей
sudo apt update
sudo apt install -y python3 python3-pip python3-venv git

# Клонирование
cd ~
git clone https://github.com/IgorTirador/Bot.git
cd Bot

# Настройка окружения
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Настройка .env
cp .env.example .env
nano .env

# Запуск в фоне
nohup python bot.py > bot.log 2>&1 &

# Просмотр логов
tail -f bot.log
```

**Управление:**

```bash
# Просмотр процесса
ps aux | grep bot.py

# Остановка
pkill -f "python.*bot.py"

# Логи
tail -f ~/Bot/bot.log
```

---

## Генерация QR-кода

После запуска бота, сгенерируйте QR-код:

```bash
cd ~/Bot
source venv/bin/activate  # Только если не используете Docker
python generate_qr.py
```

QR-код будет сохранен в `qr_codes/bot_subscription_qr.png`

### Скачивание QR-кода на локальный компьютер

```bash
# С вашего локального компьютера
scp root@185.130.115.32:~/Bot/qr_codes/bot_subscription_qr.png ./
```

---

## Настройка безопасности

### 1. Настройка firewall (UFW)

```bash
# Установка UFW
sudo apt install -y ufw

# Разрешить SSH
sudo ufw allow ssh
sudo ufw allow 22/tcp

# Включить firewall
sudo ufw enable

# Проверка статуса
sudo ufw status
```

### 2. Создание отдельного пользователя (рекомендуется)

```bash
# Создание пользователя
sudo adduser botuser

# Добавление в группу sudo (опционально)
sudo usermod -aG sudo botuser

# Переключение на нового пользователя
su - botuser

# Теперь можно клонировать репозиторий и деплоить
```

### 3. Настройка SSH ключей

На вашем **локальном компьютере**:

```bash
# Генерация SSH ключа (если нет)
ssh-keygen -t ed25519 -C "your_email@example.com"

# Копирование ключа на сервер
ssh-copy-id root@185.130.115.32
```

На **сервере**:

```bash
# Отключение аутентификации по паролю (опционально, осторожно!)
sudo nano /etc/ssh/sshd_config

# Установите:
# PasswordAuthentication no
# PubkeyAuthentication yes

# Перезапуск SSH
sudo systemctl restart sshd
```

---

## Мониторинг и обслуживание

### Проверка работы бота

**Docker:**
```bash
sudo docker-compose ps
sudo docker-compose logs --tail=50
```

**systemd:**
```bash
sudo systemctl status telegram-bot.service
sudo journalctl -u telegram-bot.service --since "10 minutes ago"
```

**Обычный процесс:**
```bash
ps aux | grep bot.py
tail -50 ~/Bot/bot.log
```

### Обновление бота

**Docker:**
```bash
cd ~/Bot
git pull
sudo docker-compose down
sudo docker-compose build
sudo docker-compose up -d
```

**systemd:**
```bash
cd ~/Bot
git pull
sudo systemctl restart telegram-bot.service
```

**Обычный процесс:**
```bash
cd ~/Bot
pkill -f "python.*bot.py"
git pull
source venv/bin/activate
pip install -r requirements.txt
nohup python bot.py > bot.log 2>&1 &
```

### Автоматическое обновление (опционально)

Создайте cron задачу для автоматического обновления:

```bash
crontab -e
```

Добавьте (обновление каждый день в 3:00):
```
0 3 * * * cd /root/Bot && git pull && docker-compose down && docker-compose build && docker-compose up -d
```

---

## Важные заметки

### ⚠️ Перед запуском бота

1. **Получите токен** у [@BotFather](https://t.me/BotFather)
2. **Создайте канал** в Telegram
3. **Добавьте бота в канал** как администратора с правами просмотра
4. **Заполните .env файл** с корректными данными

### ⚠️ Проверка подписки не работает?

**Возможные причины:**
- Бот не добавлен в канал
- Бот не имеет прав администратора
- Неверный CHANNEL_ID в .env
- CHANNEL_ID должен начинаться с @ (например: @mychannel)

**Решение:**
1. Откройте ваш канал
2. Настройки → Администраторы → Добавить администратора
3. Найдите вашего бота и добавьте
4. Дайте право "Просмотр сообщений"
5. Перезапустите бота

---

## Тестирование

После деплоя:

1. **Откройте бота** в Telegram: `https://t.me/ваш_бот_username`
2. **Отправьте** `/start`
3. **Проверьте**, что бот отвечает
4. **Нажмите** "Подписаться на канал"
5. **Подпишитесь** на канал
6. **Нажмите** "Проверить подписку"
7. **Должно прийти** сообщение со скидкой 50%

---

## Решение проблем

### Бот не запускается

```bash
# Проверьте .env файл
cat .env

# Проверьте логи
# Docker:
sudo docker-compose logs

# systemd:
sudo journalctl -u telegram-bot.service -n 100

# Обычный:
cat bot.log
```

### Бот не проверяет подписку

```bash
# Проверьте, что бот добавлен в канал
# 1. Откройте канал
# 2. Администраторы
# 3. Найдите вашего бота

# Проверьте CHANNEL_ID
cat .env | grep CHANNEL_ID

# CHANNEL_ID должен быть @username или числовой ID
```

### Нет свободного места

```bash
# Очистка Docker
sudo docker system prune -a

# Очистка apt кэша
sudo apt clean
sudo apt autoclean

# Проверка места
df -h
```

### Высокое использование памяти

```bash
# Проверка памяти
free -h

# Перезапуск бота
# Docker:
sudo docker-compose restart

# systemd:
sudo systemctl restart telegram-bot.service

# Обычный:
pkill -f "python.*bot.py"
cd ~/Bot && source venv/bin/activate && nohup python bot.py > bot.log 2>&1 &
```

---

## Полезные команды

### Проверка системы

```bash
# Проверка процессора и памяти
htop

# Проверка диска
df -h

# Проверка сети
ping google.com

# Проверка открытых портов
sudo netstat -tulpn
```

### Работа с логами

```bash
# Docker
sudo docker-compose logs -f --tail=100

# systemd
sudo journalctl -u telegram-bot.service -f
sudo journalctl -u telegram-bot.service --since today
sudo journalctl -u telegram-bot.service --since "1 hour ago"

# Файловые логи
tail -f bot.log
tail -100 bot.log
cat bot.log | grep ERROR
```

---

## Контакты и поддержка

При возникновении проблем:

1. Проверьте логи бота
2. Убедитесь в корректности .env
3. Проверьте, что бот добавлен в канал
4. Создайте issue на GitHub

---

**Успешного деплоя!** 🚀

---

## Краткая шпаргалка команд

```bash
# Подключение к серверу
ssh root@185.130.115.32

# Быстрый деплой
cd ~/Bot && ./quick-deploy.sh

# Docker команды
sudo docker-compose logs -f    # Логи
sudo docker-compose restart    # Перезапуск
sudo docker-compose down       # Остановка
sudo docker-compose up -d      # Запуск

# systemd команды
sudo systemctl status telegram-bot.service     # Статус
sudo systemctl restart telegram-bot.service    # Перезапуск
sudo journalctl -u telegram-bot.service -f     # Логи

# Обновление
cd ~/Bot && git pull && sudo docker-compose restart

# Генерация QR-кода
cd ~/Bot && python generate_qr.py

# Скачать QR-код (с локального компьютера)
scp root@185.130.115.32:~/Bot/qr_codes/bot_subscription_qr.png ./
```
