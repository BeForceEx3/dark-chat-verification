from telegram import Update
from telegram.ext import ContextTypes
from utils.storage import load_data, save_data
from config import DATA_PATH, ADMIN_ID

user_partners: dict[int, int] = {}
admin_messages: dict[int, dict[str, int]] = {}

def reload_data():
    global user_partners, admin_messages
    user_partners, admin_messages = load_data(DATA_PATH)

async def find_partner(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == ADMIN_ID:
        await update.message.reply_text('🔧 Админ не может искать партнера.')
        return
    
    reload_data()
    
    # Ищем свободного партнера
    free_users = [uid for uid, pid in user_partners.items() 
                  if pid is None or user_partners.get(pid, None) != uid]
    
    if free_users and free_users[0] != user_id:
        partner_id = free_users[0]
        user_partners[user_id] = partner_id
        user_partners[partner_id] = user_id
        save_data(DATA_PATH, user_partners, admin_messages)
        await update.message.reply_text('✅ Партнер найден! Пишите сообщения.')
        await context.bot.send_message(partner_id, '✅ Партнер найден! Пишите сообщения.')
    else:
        user_partners[user_id] = None
        save_data(DATA_PATH, user_partners, admin_messages)
        await update.message.reply_text('⏳ Ищем партнера...')

async def stop_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in user_partners:
        partner_id = user_partners.pop(user_id, None)
        if partner_id:
            user_partners.pop(partner_id, None)
            save_data(DATA_PATH, user_partners, admin_messages)
            await context.bot.send_message(partner_id, '❌ Партнер отключился.')
        await update.message.reply_text('❌ Чат завершен.')
