from flask import Flask, request, jsonify
import json
import os
from datetime import datetime
import threading
import logging

# Налаштування логування для кращої діагностики в Supervisor
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

# Шлях до файлу даних, визначений у run.sh (зазвичай /share/battery_data.json)
DATA_FILE = os.environ.get('DATA_FILE', '/share/battery_data.json')
HOST_PORT = 8099

# Назви систем
BATTERY_NAMES = {
    1: "Ліфти п2",
    2: "Вода",
    3: "Опалення"
}

# М'ютекс для безпечного доступу до файлу
file_lock = threading.Lock()

def get_initial_data():
    """Повертає початковий масив даних."""
    return [
        {"id": 1, "name": BATTERY_NAMES[1], "level": 0, "timestamp": None},
        {"id": 2, "name": BATTERY_NAMES[2], "level": 0, "timestamp": None},
        {"id": 3, "name": BATTERY_NAMES[3], "level": 0, "timestamp": None},
    ]

def load_data():
    """Завантажує дані з JSON-файлу."""
    with file_lock:
        if not os.path.exists(DATA_FILE):
            data = get_initial_data()
            save_data(data)
            return data
        
        try:
            with open(DATA_FILE, 'r') as f:
                content = f.read()
                return json.loads(content) if content else get_initial_data()
        except Exception as e:
            app.logger.error(f"Error loading data from {DATA_FILE}: {e}")
            return get_initial_data()

def save_data(data):
    """Зберігає дані в JSON-файл."""
    with file_lock:
        try:
            os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
            with open(DATA_FILE, 'w') as f:
                json.dump(data, f, indent=4)
        except IOError as e:
            app.logger.error(f"Помилка запису даних у файл: {e}")

# =================================================================
# HTML/CSS/JS КОНТЕНТ (Вбудований)
# =================================================================
# Тут використовується адаптивний HTML, який ми розробили раніше.
# Ми передаємо BATTERY_NAMES та URL API через JavaScript.

HTML_CONTENT = lambda api_url, names: f"""
<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Індикатори Енергосистеми</title>
    <style>
        :root {{
            --primary-color: #007bff;
            --success-color: #5cb85c;
            --warning-color: #f0ad4e;
            --danger-color: #d9534f;
            --bg-color: #f8f9fa;
            --card-bg: #ffffff;
            --text-color: #333;
        }}
        body {{ 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            display: flex; 
            flex-direction: column; 
            align-items: center; 
            justify-content: flex-start; 
            min-height: 100vh; 
            margin: 0; 
            padding: 20px 10px;
            background-color: var(--bg-color); 
            color: var(--text-color);
        }}
        h1 {{ 
            margin-bottom: 30px; 
            font-size: 1.8em;
            text-align: center;
        }}
        .battery-grid {{ 
            display: flex; 
            gap: 20px; 
            flex-wrap: wrap; 
            justify-content: center;
            width: 100%;
            max-width: 1000px;
        }}
        .indicator-unit {{ 
            display: flex; 
            flex-direction: column; 
            align-items: center; 
            padding: 20px; 
            border: 1px solid #e0e0e0; 
            border-radius: 12px; 
            background: var(--card-bg); 
            box-shadow: 0 4px 12px rgba(0,0,0,0.08); 
            transition: transform 0.2s;
            width: calc(33.33% - 20px);
            box-sizing: border-box;
        }}
        .indicator-unit:hover {{
            transform: translateY(-3px);
            box-shadow: 0 6px 15px rgba(0,0,0,0.1);
        }}
        .system-title {{
            font-size: 1.3em;
            margin-bottom: 15px;
            font-weight: 600;
        }}
        .battery-container {{ 
            width: 160px; 
            height: 80px; 
            border: 3px solid var(--text-color); 
            border-radius: 10px; 
            position: relative; 
            display: flex; 
            align-items: center; 
            justify-content: center; 
            margin-top: 10px; 
            background-color: #f0f0f0; 
        }}
        .battery-container::after {{ 
            content: ''; 
            position: absolute; 
            right: -10px; 
            top: 50%; 
            transform: translateY(-50%); 
            width: 8px; 
            height: 20px; 
            background-color: var(--text-color); 
            border-radius: 0 4px 4px 0; 
        }}
        .battery-level {{ 
            font-size: 2.8em; 
            font-weight: bold; 
            color: var(--text-color); 
            transition: color 0.3s;
        }}
        .timestamp-text {{ 
            margin-top: 15px; 
            font-size: 0.85em; 
            color: #777; 
            text-align: center; 
        }}
        .color-success {{ color: var(--success-color) !important; }}
        .color-warning {{ color: var(--warning-color) !important; }}
        .color-danger {{ color: var(--danger-color) !important; }}
        
        @media (max-width: 768px) {{
            .indicator-unit {{
                width: calc(50% - 15px);
            }}
        }}
        @media (max-width: 500px) {{
            .indicator-unit {{
                width: 100%;
                max-width: 300px;
            }}
            .battery-container {{
                width: 100%;
            }}
        }}
    </style>
</head>
<body>
    <h1>Рівні заряду систем:</h1>
    <div class="battery-grid" id="battery-grid">
        </div>

    <script>
        const BATTERY_NAMES = {json.dumps(names)}; 
        const API_URL = '{api_url}'; 
        const grid = document.getElementById('battery-grid');

        // Створення HTML-елементів
        for (const id in BATTERY_NAMES) {{
            const name = BATTERY_NAMES[id];
            const unit = document.createElement('div');
            unit.className = 'indicator-unit';
            unit.innerHTML = `
                <h2 class="system-title">${{name}}</h2>
                <div class="battery-container" id="container-${{id}}">
                    <div class="battery-level" id="level-${{id}}">--%</div>
                </div>
                <div class="timestamp-text" id="time-${{id}}">Останнє оновлення: Н/Д</div>
            `;
            grid.appendChild(unit);
        }}

        function formatTimestamp(isoString) {{
            if (!isoString) return 'Н/Д';
            try {{
                const date = new Date(isoString);
                return date.toLocaleDateString('uk-UA') 
                    + ' ' 
                    + date.toLocaleTimeString('uk-UA');
            }} catch (e) {{
                return 'Невірний формат часу';
            }}
        }}

        async function updateBatteryStatus() {{
            try {{
                const response = await fetch(API_URL);
                if (!response.ok) {{
                    throw new Error(`Помилка HTTP! Статус: ${{response.status}}`);
                }}
                const batteries = await response.json(); 

                batteries.forEach(data => {{
                    const {{ id, level, timestamp }} = data; 
                    const levelEl = document.getElementById(`level-${{id}}`);
                    const timeEl = document.getElementById(`time-${{id}}`);

                    if (levelEl) {{
                        levelEl.textContent = `${{level}}%`;
                        timeEl.textContent = `Оновлено: ${{formatTimestamp(timestamp)}}`;

                        // Кольорова індикація
                        levelEl.classList.remove('color-success', 'color-warning', 'color-danger');
                        if (level <= 20) {{
                            levelEl.classList.add('color-danger'); 
                        }} else if (level <= 50) {{
                            levelEl.classList.add('color-warning'); 
                        }} else {{
                            levelEl.classList.add('color-success'); 
                        }}
                    }}
                }});

            }} catch (error) {{
                console.error('Помилка при отриманні даних:', error);
                // Оновлення всіх статусів у разі помилки
                for (const id in BATTERY_NAMES) {{
                    const levelEl = document.getElementById(`level-${{id}}`);
                    const timeEl = document.getElementById(`time-${{id}}`);
                    if (levelEl) {{
                        levelEl.textContent = 'Пом.';
                        levelEl.classList.remove('color-success', 'color-warning');
                        levelEl.classList.add('color-danger'); 
                    }}
                    if (timeEl) {{
                         timeEl.textContent = 'Помилка мережі';
                    }}
                }}
            }}
        }}

        updateBatteryStatus(); 
        setInterval(updateBatteryStatus, 5000); 
    </script>
</body>
</html>
"""

# =================================================================
# ОБРОБНИКИ FLASK
# =================================================================

@app.route('/')
def index():
    """Віддає адаптивну HTML-сторінку з індикаторами."""
    # API_URL - це шлях до ендпоінту даних, відносний до кореня
    api_url = "/data" 
    
    return HTML_CONTENT(api_url, BATTERY_NAMES)

@app.route('/data', methods=['GET'])
def get_battery_data():
    """Віддає JSON-дані про стан батарей для фронтенду."""
    data = load_data()
    return jsonify(data)

@app.route('/data', methods=['POST'])
def update_battery_data():
    """Приймає POST-запит (id, level) і оновлює JSON-файл."""
    if not request.is_json:
        app.logger.warning("POST request received without JSON content.")
        return jsonify({"error": "Missing JSON in request"}), 400
    
    update_data = request.get_json()
    battery_id = update_data.get('id')
    level = update_data.get('level')

    try:
        battery_id = int(battery_id)
        level = int(level)
    except (ValueError, TypeError):
        return jsonify({"error": "ID and Level must be integers"}), 400

    if battery_id not in BATTERY_NAMES or level is None:
        return jsonify({"error": "Invalid or missing 'id' (1, 2, or 3) or 'level'."}), 400

    batteries = load_data()
    
    found = False
    for battery in batteries:
        if battery['id'] == battery_id:
            battery['level'] = level
            battery['timestamp'] = datetime.utcnow().isoformat()
            found = True
            break
            
    if found:
        save_data(batteries)
        app.logger.info(f"Battery {BATTERY_NAMES[battery_id]} updated to {level}%")
        return jsonify({"status": "updated", "id": battery_id, "name": BATTERY_NAMES[battery_id]}), 200
    else:
        return jsonify({"error": f"Battery with ID {battery_id} not found."}), 404

# Додаємо обробку CORS (хоча тунель зазвичай робить це непотрібним)
@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

if __name__ == '__main__':
    # Запускаємо сервер на визначеному порту 0.0.0.0
    app.run(host='0.0.0.0', port=HOST_PORT)
