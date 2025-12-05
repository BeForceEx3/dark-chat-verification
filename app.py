from flask import Flask, request, jsonify, render_template_string
import os
from dotenv import load_dotenv
import sqlite3, hashlib, random
from datetime import datetime, timedelta

load_dotenv()
app = Flask(__name__)

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

class ScreenCodeAuth:
    def generate_code(self):
        return str(random.randint(100000, 999999))
    
    def hash_email(self, email):
        return hashlib.sha256(email.lower().encode()).hexdigest()
    
    def send_code(self, email):
        code = self.generate_code()
        email_hash = self.hash_email(email)
        expires_at = (datetime.now() + timedelta(minutes=10)).strftime('%Y-%m-%d %H:%M:%S')
        
        conn = sqlite3.connect('codes.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO codes (email_hash, code, expires_at, attempts)
            VALUES (?, ?, ?, 0)
        ''', (email_hash, code, expires_at))
        conn.commit()
        conn.close()
        
        return True, code  # Возвращаем код напрямую!
    
    def verify_code(self, email, code):
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
            return False, "Неверный код"
        
        conn = sqlite3.connect('codes.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute('UPDATE codes SET is_valid = 0 WHERE email_hash = ?', (email_hash,))
        conn.commit()
        conn.close()
        return True, "🎉 Авторизация успешна!"

auth = ScreenCodeAuth()

HTML_TEMPLATE = '''<!DOCTYPE html>
<html>
<head>
    <title>Dark Chat Auth</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        *{margin:0;padding:0;box-sizing:border-box;}
        body{font-family:'Segoe UI',Arial;background:linear-gradient(135deg,#0c0c0c 0%,#1a1a2e 50%,#16213e 100%);color:#e0e0e0;min-height:100vh;display:flex;justify-content:center;align-items:center;margin:0;padding:20px;}
        .form{background:rgba(0,0,0,0.95);padding:40px;border-radius:25px;max-width:450px;width:100%;text-align:center;box-shadow:0 25px 60px rgba(0,0,0,0.8);border:1px solid rgba(0,212,255,0.3);}
        h2{color:#00d4ff;margin-bottom:30px;font-size:32px;text-shadow:0 0 25px #00d4ff;}
        input{width:100%;padding:20px;margin:15px 0;background:rgba(255,255,255,0.08);border:2px solid rgba(255,255,255,0.2);border-radius:15px;color:#fff;font-size:20px;text-align:center;}
        input:focus{border-color:#00d4ff;outline:none;box-shadow:0 0 30px rgba(0,212,255,0.6);}
        button{width:100%;padding:20px;margin:15px 0;background:linear-gradient(45deg,#00d4ff,#0099cc);border:none;border-radius:15px;color:white;font-size:20px;cursor:pointer;font-weight:bold;transition:all 0.3s;}
        button:hover{transform:translateY(-3px);box-shadow:0 20px 40px rgba(0,212,255,0.5);}
        .success{color:#00ff88;background:rgba(0,255,136,0.2);padding:25px;border-radius:15px;margin:20px 0;border-left:5px solid #00ff88;font-size:18px;}
        .error{color:#ff6b6b;background:rgba(255,107,107,0.15);padding:20px;border-radius:15px;margin:20px 0;border-left:4px solid #ff6b6b;}
        .code-big{font-size:60px;font-weight:bold;color:#00ff88;background:rgba(0,255,136,0.15);padding:30px;border-radius:20px;margin:30px 0;letter-spacing:10px;text-shadow:0 0 30px #00ff88;border:3px solid rgba(0,255,136,0.4);font-family:monospace;}
        .info{font-size:16px;color:#aaa;margin:20px 0;}
        @media(max-width:480px){.form{padding:30px 20px;margin:10px;}.code-big{font-size:45px;letter-spacing:5px;padding:20px;}}
    </style>
</head>
<body>
    <div class="form">
        <h2>🌙 Dark Chat</h2>
        
        {% if step == 'code' %}
            <div class="success">✅ Ваш код авторизации:</div>
            <div class="code-big">{{ code }}</div>
            <form method="POST">
                <input type="hidden" name="email" value="{{ email }}">
                <input type="text" name="code" placeholder="🔢 Введите код выше" maxlength="6" required autofocus>
                <button>✅ Подтвердить вход</button>
            </form>
            <div class="info">Скопируйте код выше → вставьте → Enter</div>
        {% else %}
            <form method="POST">
                <input type="email" name="email" placeholder="📧 Введите email (любой)" required autofocus>
                <button>🔢 Получить код</button>
            </form>
            <div class="info">Введите любой email → получите код на этой странице!</div>
        {% endif %}
        
        {% if error %}
            <div class="error">{{ error }}</div>
        {% endif %}
        
        <div style="margin-top:25px;font-size:14px;">
            <a href="/health" style="color:#00d4ff;text-decoration:none;">API статус</a>
        </div>
    </div>

    <script>
        document.addEventListener('DOMContentLoaded',function(){
            const input=document.querySelector('input:not([type=hidden])');
            if(input){
                input.focus();
                input.addEventListener('keypress',function(e){
                    if(e.key==='Enter') this.form.submit();
                });
                if(input.name==='code'){
                    input.addEventListener('input',function(){
                        this.value=this.value.replace(/[^0-9]/g,'');
                    });
                }
            }
        });
    </script>
</body>
</html>
'''

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        
        if not email or '@' not in email:
            return render_template_string(HTML_TEMPLATE, error="Введите корректный email")
        
        code_input = request.form.get('code', '').strip()
        
        if code_input:  # Проверяем код
            if len(code_input) != 6 or not code_input.isdigit():
                return render_template_string(HTML_TEMPLATE, 
                    error="Код должен быть 6 цифр", step='code', email=email)
            success, message = auth.verify_code(email, code_input)
            return render_template_string(HTML_TEMPLATE, 
                success=message if success else None,
                error=message if not success else None,
                step='code', email=email)
        else:  # Генерируем код
            success, code = auth.send_code(email)
            return render_template_string(HTML_TEMPLATE, 
                step='code', email=email, code=code)
    
    return render_template_string(HTML_TEMPLATE)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'OK', 'mode': 'screen_code', 'ready': True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
