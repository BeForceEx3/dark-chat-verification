from flask import Flask, request, jsonify, render_template_string
import os
from dotenv import load_dotenv
import smtplib, ssl, random, sqlite3, hashlib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

load_dotenv()
app = Flask(__name__)

SMTP_EMAIL = os.getenv('SMTP_EMAIL', 'your-bot@gmail.com')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', 'abcd efgh ijkl mnop')

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

class GmailAuth:
    def generate_code(self):
        return str(random.randint(100000, 999999))
    
    def hash_email(self, email):
        return hashlib.sha256(email.lower().encode()).hexdigest()
    
    def send_code(self, email):
        """Gmail SMTP - работает на Render!"""
        if not SMTP_EMAIL or not SMTP_PASSWORD:
            return False, "SMTP настройки не заданы"
        
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
        
        # ✅ Gmail SMTP (ИСПРАВЛЕНО!)
        try:
            msg = MIMEMultipart()
            msg['From'] = SMTP_EMAIL
            msg['To'] = email
            msg['Subject'] = '🔐 Код авторизации Dark Chat'
            
            body = f"""Ваш код авторизации Dark Chat:

🔢 Код: {code}

⏰ Действует 10 минут
👉 Введите код на сайте для входа."""
            
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # ✅ КЛЮЧЕВОЕ ИСПРАВЛЕНИЕ: без context!
            server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.sendmail(SMTP_EMAIL, email, msg.as_string())
            server.quit()
            
            print(f"✅ Gmail: {email} → {code}")
            return True, "Код отправлен на почту!"
            
        except Exception as e:
            print(f"❌ Gmail ошибка: {e}")
            return False, f"Ошибка отправки: {str(e)}"
    
    def verify_code(self, email, code):
        email_hash = self.hash_email(email)
        conn = sqlite3.connect('codes.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute('SELECT code, is_valid, attempts, expires_at FROM codes WHERE email_hash = ?', (email_hash,))
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            return False, "Код не найден"
        
        stored_code, is_valid, attempts, expires_at = result
        
        if datetime.now() > datetime.strptime(expires_at, '%Y-%m-%d %H:%M:%S'):
            conn.close()
            return False, "Код истек"
        
        if stored_code != code:
            conn.close()
            return False, "Неверный код"
        
        cursor.execute('UPDATE codes SET is_valid = 0 WHERE email_hash = ?', (email_hash,))
        conn.commit()
        conn.close()
        return True, "✅ Добро пожаловать в Dark Chat!"

auth = GmailAuth()

HTML_TEMPLATE = '''<!DOCTYPE html>
<html><head><title>Dark Chat</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
* {margin:0;padding:0;box-sizing:border-box;}
body {font-family:Segoe UI,Arial;background:linear-gradient(135deg,#0c0c0c 0%,#1a1a2e 50%,#16213e 100%);color:#e0e0e0;height:100vh;display:flex;justify-content:center;align-items:center;margin:0;}
.form {background:rgba(0,0,0,0.95);padding:40px;border-radius:25px;min-width:380px;text-align:center;box-shadow:0 25px 50px rgba(0,0,0,0.8);border:1px solid rgba(0,212,255,0.3);}
h2 {color:#00d4ff;margin-bottom:30px;font-size:28px;text-shadow:0 0 20px #00d4ff;}
input {width:100%;padding:18px;margin:15px 0;background:rgba(255,255,255,0.08);border:2px solid rgba(255,255,255,0.15);border-radius:15px;color:#fff;font-size:20px;text-align:center;}
input:focus {border-color:#00d4ff;outline:none;box-shadow:0 0 25px rgba(0,212,255,0.5);}
button {width:100%;padding:18px;margin:15px 0;background:linear-gradient(45deg,#00d4ff,#0099cc);border:none;border-radius:15px;color:white;font-size:18px;cursor:pointer;font-weight:bold;}
button:hover {transform:translateY(-3px);box-shadow:0 15px 35px rgba(0,212,255,0.5);}
.error {color:#ff6b6b;background:rgba(255,107,107,0.15);padding:15px;border-radius:10px;margin:15px 0;border-left:4px solid #ff6b6b;}
.success {color:#51cf66;background:rgba(81,207,102,0.15);padding:15px;border-radius:10px;margin:15px 0;border-left:4px solid #51cf66;}
.info {font-size:14px;color:#aaa;margin-top:20px;}
</style></head>
<body>
<div class="form">
<h2>🌙 Dark Chat</h2>
{% if step == "code" %}
<div class="success">✅ Код отправлен на <b>{{ email }}</b></div>
<form method="POST">
<input type="hidden" name="email" value="{{ email }}">
<input type="text" name="code" placeholder="🔢 6-значный код" maxlength="6" required autofocus>
<button>✅ Войти в чат</button>
</form>
<div class="info">Проверьте почту (включая Спам). Код действует 10 минут.</div>
{% else %}
<form method="POST">
<input type="email" name="email" placeholder="📧 Любой email" required autofocus>
<button>📧 Отправить код</button>
</form>
<div class="info">Введите email → получите 6-значный код на почту</div>
{% endif %}
{% if error %}<div class="error">{{ error }}</div>{% endif %}
<div style="margin-top:20px;font-size:12px;"><a href="/health" style="color:#00d4ff;text-decoration:none;">API статус</a></div>
</div>
<script>
document.addEventListener("DOMContentLoaded",function(){
    const input=document.querySelector("input");if(input){input.focus();input.addEventListener("keypress",function(e){if(e.key==="Enter")this.form.submit();});}
    const codeInput=document.querySelector('input[name="code"]');if(codeInput){codeInput.addEventListener("input",function(){this.value=this.value.replace(/[^0-9]/g,"");});}
});
</script>
</body></html>'''

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        code = request.form.get('code', '').strip()
        
        if not email or '@' not in email:
            return render_template_string(HTML_TEMPLATE, error="Неверный email")
        
        if code:
            if len(code) != 6 or not code.isdigit():
                return render_template_string(HTML_TEMPLATE, error="Код должен быть 6 цифр", step='code', email=email)
            success, message = auth.verify_code(email, code)
            return render_template_string(HTML_TEMPLATE, 
                success=message if success else None,
                error=message if not success else None,
                step='code', email=email)
        else:
            success, message = auth.send_code(email)
            if success:
                return render_template_string(HTML_TEMPLATE, step='code', email=email)
            return render_template_string(HTML_TEMPLATE, error=message)
    
    return render_template_string(HTML_TEMPLATE)

@app.route('/send_code', methods=['POST'])
def send_code_api():
    data = request.get_json() or {}
    email = data.get('email', '').strip()
    if not email or '@' not in email:
        return jsonify({'error': 'Неверный email'}), 400
    success, message = auth.send_code(email)
    return jsonify({'success': success, 'message': message})

@app.route('/verify_code', methods=['POST'])
def verify_code_api():
    data = request.get_json() or {}
    email = data.get('email', '').strip()
    code = data.get('code', '').strip()
    if len(code) != 6 or not code.isdigit():
        return jsonify({'success': False, 'message': 'Код должен быть 6 цифр'}), 400
    success, message = auth.verify_code(email, code)
    return jsonify({'success': success, 'message': message})

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'OK', 
        'gmail_ready': bool(SMTP_EMAIL and SMTP_PASSWORD),
        'smtp_email': SMTP_EMAIL if SMTP_EMAIL else 'NOT_SET'
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
