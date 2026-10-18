# Исходный образ: официальный образ Python 3.11
FROM python:3.11-slim

# Не создавать .pyc и выводить логи сразу
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Устанавливаем зависимости
RUN pip install --upgrade pip
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем проект Django (medtracker) и приложение (analyses)
COPY . .

# Порт web-сервера
EXPOSE 8000

# При запуске применяем миграции и запускаем сервер Django
CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py runserver 0.0.0.0:8000"]
