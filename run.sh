#!/usr/bin/env bash

echo "Starting HA Battery Monitor Addon with Cloudflare Tunnel..."

# Шляхи
export DATA_FILE=/share/battery_data.json
export CONFIG_FILE=/etc/cloudflared/config.yml

# ----------------------------------------------------------------
# 1. Запуск Flask-сервера
# ----------------------------------------------------------------
echo "Starting Flask server on port 8099 in background..."
python3 /app/app.py &

# Зберігаємо PID Flask-сервера
FLASK_PID=$!

# ----------------------------------------------------------------
# 2. Налаштування та запуск Cloudflare Tunnel
# ----------------------------------------------------------------

# Перевірка наявності токена
if [ -z "$CLOUDFLARED_TOKEN" ]; then
    echo "ERROR: Cloudflared token (CLOUDFLARED_TOKEN) is not set in secrets!"
    exit 1
fi

# Отримуємо ID тунелю, якщо він існує
if [ -f /etc/cloudflared/creds.json ]; then
    export TUNNEL_ID=$(jq -r '.TunnelID' /etc/cloudflared/creds.json)
    if [ -z "$TUNNEL_ID" ] || [ "$TUNNEL_ID" == "null" ]; then
        echo "ERROR: Tunnel ID could not be extracted from creds.json."
        exit 1
    fi
else
    echo "ERROR: Cloudflared credentials file not found. Did you set it up correctly?"
    echo "You must manually place the creds.json file in the addon's /share/ folder."
    exit 1
fi

echo "Tunnel ID found: $TUNNEL_ID"

# Замінюємо плейсхолдери у конфігураційному файлі cloudflared.yml
sed -i "s/\${TUNNEL_ID}/$TUNNEL_ID/" $CONFIG_FILE
sed -i "s/\${TUNNEL_DOMAIN}/$TUNNEL_DOMAIN/" $CONFIG_FILE

echo "Starting Cloudflared Tunnel..."

# Запускаємо cloudflared. Використовуємо exec для того, щоб cloudflared 
# став головним процесом, і Supervisor міг контролювати контейнер.
exec cloudflared tunnel run
