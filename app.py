from flask import Flask, request, jsonify, render_template_string
import os
from dotenv import load_dotenv
import smtplib, ssl, random, sqlite3, hashlib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

load_dotenv()
app = Flask(__name__)

# ✅ База только для кодов (НЕ пользователей!)
def init_codes_db():
    conn = sqlite3.connect('codes.db', check_same_thread=False)
    conn.execute('''CREATE TABLE IF NOT EXISTS codes (
        id INTEGER PRIMARY KEY,
        email_hash TEXT UNIQUE NOT NULL,
        code TEXT NOT NULL,
        is_valid INTEGER DEFAULT 1,
        attempts INTEGER DEFAULT 0,
        expires_at TEXT
    )''')
    conn.commit()
    conn.close()

init_codes_db()

class SimpleEmailAuth:
    def __init__(self):
        self.smtp_email = os.getenv('SMTP_EMAIL')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
    
    def generate_code(self):
        return str(random.randint(100000, 999999))
    
    def hash_email(self, email):
        return hashlib.sha256(email.lower().encode()).hexdigest()
    
    def send_code(self, email):
        """Отправляет код ЛЮБОМУ email!"""
        if not self.smtp_email or not self.smtp_password:
            return False, "SMTP не настроен"
        
        code = self.generate_code()
        email_hash = self.hash_email(email)
        expires_at = (datetime.now() + timedelta(minutes=10)).strftime('%Y-%m-%d %H:%M:%S')
        
        # Сохраняем код
        conn = sqlite3.connect('codes.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO codes (email_hash, code, expires_at, attempts)
            VALUES (?, ?, ?, 0)
        ''', (email_hash, code, expires_at))
        conn.commit()
        conn.close()
        
        # Отправляем
        try:
            msg = MIMEMultipart()
            msg['From'] = self.smtp_email
            msg['To'] = email
            msg['Subject'] = '🔐 Код авторизации Dark Chat'
            
            body = f"""Ваш код авторизации Dark Chat:

🔢 Код: {code}

⏰ Действует 10 минут
👉 Введите код на сайте для входа."""
            
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as server:
                server.login(self.smtp_email, self.smtp_password)
                server.sendmail(self.smtp_email, email, msg.as_string())
            
            return True, f"Код отправлен на {email}"
            
        except Exception as e:
            return False, f"Ошибка: {str(e)}"
    
    def verify_code(self, email, code):
        """Проверяет код"""
        email_hash = self.hash_email(email)
        
        conn = sqlite3.connect('codes.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute('SELECT code, is_valid, attempts, expires_at FROM codes WHERE email_hash = ?', (email_hash,))
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return False, "Код не найден"
        
        stored_code, is_valid, attempts, expires_at = result
        
        if datetime.now() > datetime.strptime(expires_at, '%Y-%m-%d %H:%M:%S'):
            return False, "Код истек"
        
        if stored_code != code:
            # Блокируем после 5 попыток
            if attempts + 1 >= 5:
                cursor.execute('UPDATE codes SET is_valid = 0 WHERE email_hash = ?', (email_hash,))
                conn.commit()
                conn.close()
                return False, "Слишком много попыток"
            return False, "Неверный код"
        
        # Успех! Блокируем код
        cursor.execute('UPDATE codes SET is_valid = 0 WHERE email_hash = ?', (email_hash,))
        conn.commit()
        conn.close()
        return True, "✅ Авторизация успешна!"

auth = SimpleEmailAuth()

# ✅ Главная страница с вводом кода
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Dark Chat - Код авторизации</title>
    <style>
        body { 
            font-family: Arial; 
            background: linear-gradient(135deg, #0c0c0c 0%, #1a1a2e 50%);
            color: #e0e0e0; height: 100vh; display: flex; 
            justify-content: center; align-items: center; margin: 0;
        }
        .form { 
            background: rgba(0,0,0,0.9); padding: 40px; 
            border-radius: 20px; min-width: 350px; text-align: center;
        }
        h2 { color: #00d4ff; margin-bottom: 30px; }
        input { 
            width: 100%; padding: 15px; margin: 10px 0; 
            background: rgba(255,255,255,0.05); border: 2px solid rgba(255,255,255,0.1); 
            border-radius: 10px; color: #fff; font-size: 20px; text-align: center;
        }
        button { 
            width: 100%; padding: 15px; margin: 10px 0; 
            background: linear-gradient(45deg, #00d4ff, #0099cc); 
            border: none; border-radius: 10px; color: white; font-size: 16px; cursor: pointer;
        }
        .error { color: #ff4444; background: #ffe6e6; padding: 10px; border-radius: 5px; margin: 10px 0; }
        .success { color: #44ff44; background: #e6ffe6; padding: 10px; border-radius: 5px; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="form">
        <h2>🌙 Dark Chat</h2>
        {% if step == 'code' %}
            <div class="success">Код отправлен на {{ email }}!</div>
            <form method="POST">
                <input type="hidden" name="email" value="{{ email }}">
                <input type="text" name="code" placeholder="🔢 Введите 6-значный код" maxlength="6" required>
                <button type="submit">✅ Подтвердить</button>
            </form>
        {% else %}
            <form method="POST">
                <input type="email" name="email" placeholder="📧 Любой email" required>
                <button type="submit">📧 Отправить код</button>
            </form>
        {% endif %}
        {% if error %}
            <div class="error">{{ error }}</div>
        {% endif %}
    </div>
</body>
</html>
'''

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        code = request.form.get('code', '').strip()
        
        if code:  # Проверяем код
            if '@' not in email:
                return render_template_string(HTML_TEMPLATE, error="Неверный email", step='code', email=email)
            success, message = auth.verify_code(email, code)
            return render_template_string(HTML_TEMPLATE, 
                error=message if not success else None,
                success=message if success else None,
                step='code', email=email)
        else:  # Отправляем код
            if '@' not in email:
                return render_template_string(HTML_TEMPLATE, error="Неверный email")
            success, message = auth.send_code(email)
            return render_template_string(HTML_TEMPLATE, step='code', email=email)
    
    return render_template_string(HTML_TEMPLATE)

@app.route('/send_code', methods=['POST'])
def send_code():
    data = request.get_json() or {}
    email = data.get('email', '').strip()
    if not email or '@' not in email:
        return jsonify({'error': 'Неверный email'}), 400
    success, message = auth.send_code(email)
    return jsonify({'success': success, 'message': message})

@app.route('/verify_code', methods=['POST'])
def verify_code():
    data = request.get_json() or {}
    success, message = auth.verify_code(data.get('email'), data.get('code'))
    return jsonify({'success': success, 'message': message})

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'OK'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
