from telegram import Update
from telegram.ext import ContextTypes
from config import ADMIN_ID

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == ADMIN_ID:
        await update.message.reply_text('🔧 Админ-панель: бот запущен. Все сообщения доступны.')
    else:
        await update.message.reply_text(
            '👻 Добро пожаловать в анонимный чат!\n'
            '📱 /find - найти партнера для чата\n'
            '❌ /stop - завершить чат'
        )
