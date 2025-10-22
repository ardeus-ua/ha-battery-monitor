from flask import Flask, request, jsonify, render_template, abort
import json
import os
from datetime import datetime
import threading

app = Flask(__name__)

# Шлях до файлу даних, визначений у run.sh
DATA_FILE = os.environ.get('DATA_FILE', '/share/battery_data.json')
# Порт для запуску
HOST_PORT = 8099

# Назви систем
BATTERY_NAMES = {
    1: "Ліфти",
    2: "Вода",
    3: "Опалення"
}

# М'ютекс для безпечного доступу до файлу з кількох потоків
file_lock = threading.Lock()

def get_initial_data():
    """Повертає початковий масив даних."""
    return [
        {"id": 1, "name": BATTERY_NAMES[1], "level": 0, "timestamp": None},
        {"id": 2, "name": BATTERY_NAMES[2], "level": 0, "timestamp": None},
        {"id": 3, "name": BATTERY_NAMES[3], "level": 0, "timestamp": None},
    ]

def load_data():
    """Завантажує дані з JSON-файлу або ініціалізує, якщо файл не існує."""
    with file_lock:
        if not os.path.exists(DATA_FILE):
            # Якщо файл не існує, створюємо його з початковими даними
            data = get_initial_data()
            save_data(data)
            return data
        
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # У разі помилки читання або порожнього файлу, ініціалізуємо
            data = get_initial_data()
            save_data(data)
            return data

def save_data(data):
    """Зберігає дані в JSON-файл."""
    with file_lock:
        try:
            # Створюємо директорію, якщо вона не існує
            os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
            with open(DATA_FILE, 'w') as f:
                json.dump(data, f, indent=4)
        except IOError as e:
            app.logger.error(f"Помилка запису даних у файл: {e}")

# =================================================================
# WEB-ІНТЕРФЕЙС
# =================================================================

# Цей ендпоінт віддає HTML-сторінку
@app.route('/')
def index():
    """Віддає адаптивну HTML-сторінку з індикаторами."""
    # API_URL - це шлях до ендпоінту даних, відносний до кореня
    api_url = "/data" 
    
# Викликаємо функцію, що містить весь HTML/CSS/JS (повинна бути визначена вище)
    return HTML_CONTENT(api_url)
# =================================================================
# API ЕНДПОІНТИ
# =================================================================

# Ендпоінт для читання даних (GET)
@app.route('/data', methods=['GET'])
def get_battery_data():
    """Віддає JSON-дані про стан батарей для фронтенду."""
    data = load_data()
    return jsonify(data)

# Ендпоінт для оновлення даних (POST від датчиків/HA)
@app.route('/data', methods=['POST'])
def update_battery_data():
    """Приймає POST-запит (id, level) і оновлює JSON-файл."""
    if not request.is_json:
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
        return jsonify({"status": "updated", "id": battery_id, "name": BATTERY_NAMES[battery_id]}), 200
    else:
        # Цей випадок має бути неможливим, якщо load_data працює коректно
        return jsonify({"error": f"Battery with ID {battery_id} not found."}), 404

# Додаємо обробку CORS для можливості доступу з іншого домену/порту (хоча в HA це рідко потрібно)
@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

if __name__ == '__main__':
    # Flask шукає HTML-шаблони у папці 'templates'
    # Оскільки ми використовуємо `render_template` без папки 'templates',
    # ми генеруємо HTML безпосередньо в коді.
    # Запускаємо сервер на визначеному порту
    app.run(host='0.0.0.0', port=HOST_PORT)
