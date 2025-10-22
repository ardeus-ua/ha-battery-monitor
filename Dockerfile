# Використовуємо мінімальний Python-образ
FROM python:3.9-slim

# Встановлюємо робочий каталог
WORKDIR /app

# 1. Встановлення базових утиліт та Python-залежностей
RUN apt-get update && apt-get install -y \
    wget \
    ca-certificates \
    jq \
    && pip install Flask \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 2. Встановлення Cloudflared
# Визначаємо аргумент для архітектури (значення підставляється з config.yaml)
ARG ARCH=amd64 
RUN wget -q -O /usr/local/bin/cloudflared "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-$ARCH" \
    && chmod +x /usr/local/bin/cloudflared

# 3. Копіювання файлів
# Копіюємо Python-код із підпапки battery_server
COPY battery_server/app.py /app/app.py 
# Копіюємо конфіг cloudflared
COPY battery_server/cloudflared.yml /etc/cloudflared/config.yml 

# Порт Flask-сервера
EXPOSE 8099
