# Используем официальный образ Python
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файл зависимостей
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем все файлы проекта
COPY bot.py .
COPY generate_qr.py .
COPY database.py .

# Создаем директорию для QR-кодов
RUN mkdir -p qr_codes

# Запускаем бота
CMD ["python", "bot.py"]
