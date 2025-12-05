let ws = null;
let currentUser = null;

// Получить пароль по email
async function sendPassword() {
    const email = document.getElementById('userEmail').value.trim();
    if (!email || !email.includes('@')) {
        showStatus('Введите корректный email', 'error');
        return;
    }

    try {
        showStatus('Отправляем пароль...', 'loading');
        const response = await fetch('https://your-verification-app.onrender.com/send_password', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({email})
        });
        
        const data = await response.json();
        
        if (data.success) {
            showStatus('✅ Пароль отправлен на ' + email, 'success');
        } else {
            showStatus('❌ ' + data.message, 'error');
        }
    } catch (error) {
        showStatus('❌ Ошибка сети', 'error');
    }
}

// Вход в чат
async function login() {
    const email = document.getElementById('userEmail').value.trim();
    const password = document.getElementById('userPassword').value.trim();
    
    if (!email || !password) {
        showStatus('Введите email и пароль', 'error');
        return;
    }

    try {
        const response = await fetch('https://your-verification-app.onrender.com/login', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({email, password})
        });
        
        const data = await response.json();
        
        if (data.success) {
            currentUser = email;
            document.getElementById('loginForm').style.display = 'none';
            document.getElementById('chatContainer').style.display = 'flex';
            connectWebSocket();
            showStatus(`Привет, ${email}!`, 'success');
        } else {
            showStatus('❌ Неверный пароль', 'error');
        }
    } catch (error) {
        showStatus('❌ Ошибка входа', 'error');
    }
}

// WebSocket чат (демо)
function connectWebSocket() {
    // Замените на ваш WebSocket URL
    ws = new WebSocket('wss://your-chat-ws.onrender.com');
    
    ws.onopen = () => {
        showStatus('🟢 Подключен к чату', 'success');
        ws.send(JSON.stringify({type: 'join', user: currentUser}));
    };
    
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        addMessage(data.user || 'Система', data.message, data.user === currentUser ? 'sent' : 'received');
    };
    
    ws.onclose = () => showStatus('🔴 Отключен от чата', 'warning');
}

// Отправить сообщение
function sendMessage() {
    const input = document.getElementById('messageInput');
    const message = input.value.trim();
    
    if (message && ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
            type: 'message',
            user: currentUser,
            message: message
        }));
        input.value = '';
    }
}

// Enter для отправки
function handleKeyPress(event) {
    if (event.key === 'Enter') {
        sendMessage();
    }
}

// Добавить сообщение в чат
function addMessage(user, text, type = 'received') {
    const messages = document.getElementById('messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    messageDiv.innerHTML = `<strong>${user}:</strong> ${text}`;
    messages.appendChild(messageDiv);
    messages.scrollTop = messages.scrollHeight;
}

// Статус сообщения
function showStatus(text, type = 'info') {
    const status = document.getElementById('loginStatus');
    status.textContent = text;
    status.className = type;
    setTimeout(() => status.textContent = '', 5000);
}
