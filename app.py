from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import requests
import base64
from datetime import datetime
import threading

app = Flask(__name__)
CORS(app)

# GitHub токен
GITHUB_TOKEN = "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"
GITHUB_REPO = "vetnamdod-boop/klyukvagram-backend"
GITHUB_BASE_URL = "https://api.github.com"

# Папка для локальных данных
DATA_DIR = r"C:\Users\Муканожечка\Desktop\сервер\data"
os.makedirs(DATA_DIR, exist_ok=True)
USERS_FILE = os.path.join(DATA_DIR, "users.json")
CHATS_FILE = os.path.join(DATA_DIR, "chats.json")

# Инициализация файлов
if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump({}, f)
        print(f"Создан пустой файл {USERS_FILE}")

if not os.path.exists(CHATS_FILE):
    with open(CHATS_FILE, 'w', encoding='utf-8') as f:
        json.dump({}, f)
        print(f"Создан пустой файл {CHATS_FILE}")

def load_json(file_path):
    """Загрузка JSON файла"""
    try:
        if not os.path.exists(file_path):
            print(f"Файл {file_path} не существует, возвращаем пустой словарь")
            return {}
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                print(f"Файл {file_path} пуст, возвращаем пустой словарь")
                return {}
            return json.loads(content)
    except json.JSONDecodeError as e:
        print(f"Ошибка парсинга JSON в {file_path}: {e}")
        return {}
    except Exception as e:
        print(f"Ошибка чтения файла {file_path}: {e}")
        return {}

def save_json(file_path, data):
    """Сохранение JSON файла"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Файл {file_path} успешно сохранён")
    except Exception as e:
        print(f"Ошибка сохранения файла {file_path}: {e}")

def upload_to_github(file_path, content, message="Update data"):
    """Загрузка файла на GitHub"""
    try:
        file_name = os.path.basename(file_path)
        url = f"{GITHUB_BASE_URL}/repos/{GITHUB_REPO}/contents/data/{file_name}"
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        # Получаем текущую версию файла
        response = requests.get(url, headers=headers)
        sha = None
        if response.status_code == 200:
            current_file = response.json()
            sha = current_file['sha']
            print(f"Получен SHA для {file_name}: {sha}")

        # Кодируем содержимое в base64
        encoded_content = base64.b64encode(content.encode('utf-8')).decode('utf-8')

        # Загружаем новый файл
        payload = {
            "message": message,
            "content": encoded_content,
            "sha": sha if sha else None
        }
        
        response = requests.put(url, headers=headers, json=payload)
        if response.status_code in (200, 201):
            print(f"Файл {file_name} успешно загружен на GitHub")
            return True
        else:
            print(f"Ошибка загрузки на GitHub: {response.status_code}, {response.text}")
            return False
    except Exception as e:
        print(f"Ошибка при загрузке на GitHub: {e}")
        return False

def get_github_file(file_path):
    """Получение файла с GitHub"""
    try:
        file_name = os.path.basename(file_path)
        url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/data/{file_name}"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Ошибка получения файла с GitHub: {response.status_code}")
            return None
    except Exception as e:
        print(f"Ошибка при получении файла с GitHub: {e}")
        return None

def upload_data_to_github_async(file_path, data, message="Update data"):
    """Асинхронная загрузка на GitHub"""
    def upload_thread():
        content = json.dumps(data, ensure_ascii=False, indent=2)
        success = upload_to_github(file_path, content, message)
        if success:
            # Удаляем локальный файл только после успешной загрузки
            try:
                os.remove(file_path)
                print(f"Локальный файл {file_path} удалён")
            except OSError as e:
                print(f"Ошибка удаления локального файла {file_path}: {e}")
    
    thread = threading.Thread(target=upload_thread)
    thread.start()

# API для авторизации
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    login = data.get('login')
    password = data.get('password')
    
    users = load_json(USERS_FILE) or get_github_file(USERS_FILE) or {}
    
    if login in users and users[login]['password'] == password:
        user_data = {
            'login': login,
            'token': f"token_{login}_{datetime.now().timestamp()}",
            'timestamp': datetime.now().isoformat()
        }
        users[login]['last_login'] = datetime.now().isoformat()
        users[login]['token'] = user_data['token']
        save_json(USERS_FILE, users)
        
        # Загружаем на GitHub
        upload_data_to_github_async(USERS_FILE, users, "User login")
        
        return jsonify({
            'success': True,
            'message': 'Успешный вход',
            'user_data': user_data
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Неверный логин или пароль'
        }), 401

# API для регистрации
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    login = data.get('login')
    password = data.get('password')
    
    users = load_json(USERS_FILE) or get_github_file(USERS_FILE) or {}
    
    if login in users:
        return jsonify({
            'success': False,
            'message': 'Пользователь уже существует'
        })
    
    if len(login) < 4 or len(login) > 15:
        return jsonify({
            'success': False,
            'message': 'Логин должен быть от 4 до 15 символов'
        })
    
    if len(password) < 8 or len(password) > 15:
        return jsonify({
            'success': False,
            'message': 'Пароль должен быть от 8 до 15 символов'
        })
    
    users[login] = {
        'password': password,
        'registration_date': datetime.now().isoformat(),
        'last_login': None,
        'token': None
    }
    
    save_json(USERS_FILE, users)
    
    # Загружаем на GitHub
    upload_data_to_github_async(USERS_FILE, users, "User registration")
    
    return jsonify({
        'success': True,
        'message': 'Регистрация успешна'
    })

# API для авто-входа
@app.route('/api/auto-login', methods=['POST'])
def auto_login():
    data = request.json
    token = data.get('token')
    
    users = load_json(USERS_FILE) or get_github_file(USERS_FILE) or {}
    
    for login, user_data in users.items():
        if user_data.get('token') == token:
            # Обновляем токен
            users[login]['token'] = f"token_{login}_{datetime.now().timestamp()}"
            users[login]['last_login'] = datetime.now().isoformat()
            save_json(USERS_FILE, users)
            
            # Загружаем на GitHub
            upload_data_to_github_async(USERS_FILE, users, "Auto login")
            
            return jsonify({
                'success': True,
                'message': 'Авто-вход успешен',
                'user_data': {
                    'login': login,
                    'token': users[login]['token']
                }
            })
    
    return jsonify({
        'success': False,
        'message': 'Неверный токен'
    }), 401

# API для списка чатов
@app.route('/api/chats', methods=['GET'])
def get_chats():
    # Получаем данные с GitHub
    chats = get_github_file(CHATS_FILE) or load_json(CHATS_FILE) or {}
    return jsonify({
        'success': True,
        'chats': chats
    })

# API для отправки сообщения
@app.route('/api/send-message', methods=['POST'])
def send_message():
    data = request.json
    chat_id = data.get('chat_id')
    message = data.get('message')
    sender = data.get('sender')
    
    chats = load_json(CHATS_FILE) or get_github_file(CHATS_FILE) or {}
    
    if chat_id not in chats:
        chats[chat_id] = {
            'participants': [sender],
            'messages': []
        }
    
    message_data = {
        'id': len(chats[chat_id]['messages']) + 1,
        'sender': sender,
        'message': message,
        'timestamp': datetime.now().isoformat()
    }
    
    chats[chat_id]['messages'].append(message_data)
    save_json(CHATS_FILE, chats)
    
    # Загружаем на GitHub
    upload_data_to_github_async(CHATS_FILE, chats, "New message")
    
    return jsonify({
        'success': True,
        'message': 'Сообщение отправлено'
    })

# API для получения сообщений чата
@app.route('/api/chat/<chat_id>', methods=['GET'])
def get_chat_messages(chat_id):
    # Получаем данные с GitHub
    chats = get_github_file(CHATS_FILE) or load_json(CHATS_FILE) or {}
    
    if chat_id in chats:
        return jsonify({
            'success': True,
            'chat': chats[chat_id]
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Чат не найден'
        }), 404

# API для списка пользователей
@app.route('/api/users', methods=['GET'])
def get_users():
    # Получаем данные с GitHub
    users = get_github_file(USERS_FILE) or load_json(USERS_FILE) or {}
    user_list = [{'login': login} for login in users.keys()]
    
    return jsonify({
        'success': True,
        'users': user_list
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)