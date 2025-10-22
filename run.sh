#!/usr/bin/env bash

echo "Starting HA Battery Monitor Addon with Cloudflare Tunnel..."

# Шляхи
export DATA_FILE=/share/battery_data.json
export CONFIG_FILE=/etc/cloudflared/config.yml
# Шлях до файлу облікових даних, який користувач повинен покласти у /share
export SHARED_CREDS_FILE=/share/tunnel_creds.json 

# ----------------------------------------------------------------
# 1. Запуск Flask-сервера
# ----------------------------------------------------------------
echo "Starting Flask server on port 8099 in background..."
python3 /app/app.py &

# ЗБЕРЕЖЕННЯ PID: Це критично для коректної роботи 'wait' і 'kill'.
FLASK_PID=$!

# ----------------------------------------------------------------
# 2. Налаштування та запуск Cloudflare Tunnel
# ----------------------------------------------------------------

# Перевірка наявності необхідних змінних
if [ -z "$CLOUDFLARED_TUNNEL_ID" ] || [ -z "$TUNNEL_DOMAIN" ]; then
    echo "WARNING: Cloudflare Tunnel secrets (ID and DOMAIN) are not set."
    echo "Skipping tunnel startup. Access the web interface via http://<HA_IP>:8099."
    # Якщо тунель не запускається, чекаємо Flask і виходимо
    wait $FLASK_PID 
    exit $?
fi

export TUNNEL_ID=$CLOUDFLARED_TUNNEL_ID 

# Перевірка наявності файлу облікових даних
if [ ! -f "$SHARED_CREDS_FILE" ]; then
    echo "ERROR: Cloudflare credentials file not found at $SHARED_CREDS_FILE."
    echo "Будь ласка, розмістіть файл creds.json у папці /share/ та перейменуйте його на tunnel_creds.json."
    kill $FLASK_PID
    exit 1
fi

echo "Tunnel ID: $TUNNEL_ID"
echo "Tunnel Domain: $TUNNEL_DOMAIN"

# 1. Створення папки та копіювання облікових даних
mkdir -p /etc/cloudflared/
cp "$SHARED_CREDS_FILE" /etc/cloudflared/creds.json 

# 2. Заміна плейсхолдерів у конфігураційному файлі cloudflared.yml
sed -i "s/\${TUNNEL_ID}/$TUNNEL_ID/" $CONFIG_FILE
sed -i "s/\${TUNNEL_DOMAIN}/$TUNNEL_DOMAIN/" $CONFIG_FILE

echo "Starting Cloudflared Tunnel..."

# Запускаємо cloudflared як головний процес
exec cloudflared tunnel run --config $CONFIG_FILE
