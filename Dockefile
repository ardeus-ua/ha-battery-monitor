# Використовуємо мінімальний Python-образ
FROM python:3.9-slim

# Встановлюємо робочий каталог
WORKDIR /app

# 1. Встановлення Flask та Python-залежностей
RUN pip install Flask

# 2. Встановлення Cloudflared
# Завантажуємо статичний бінарний файл cloudflared
RUN apt-get update && apt-get install -y wget ca-certificates \
    && wget -q -O /usr/local/bin/cloudflared "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64" \
    && chmod +x /usr/local/bin/cloudflared \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Копіюємо Python-код та конфіг cloudflared
COPY app.py /app/
COPY cloudflared.yml /etc/cloudflared/config.yml

# Порт Flask-сервера
EXPOSE 8099

# Команда для запуску (викликається через run.sh)
CMD ["python3", "app.py"]
