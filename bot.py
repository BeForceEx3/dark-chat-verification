import logging
import json
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID'))
DATA_PATH = 'chat_data.json'

user_partners = {}
admin_messages = {}

def load_data():
    global user_partners, admin_messages
    if os.path.exists(DATA_PATH):
        with open(DATA_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            user_partners.update(data.get('partners', {}))
            admin_messages.update(data.get('messages', {}))

def save_data():
    data = {'partners': user_partners, 'messages': admin_messages}
    with open(DATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == ADMIN_ID:
        await update.message.reply_text('🔧 Админ: бот запущен!')
    else:
        await update.message.reply_text('👻 Анонимный чат!\n/find - найти партнера\n/stop - выйти')

async def find_partner(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == ADMIN_ID: return
    
    load_data()
    free_users = [uid for uid, pid in user_partners.items() if pid is None or user_partners.get(pid) != uid]
    
    if free_users and free_users[0] != user_id:
        partner_id = free_users[0]
        user_partners[user_id] = partner_id
        user_partners[partner_id] = user_id
        save_data()
        await update.message.reply_text('✅ Партнер найден!')
        await context.bot.send_message(partner_id, '✅ Партнер найден!')
    else:
        user_partners[user_id] = None
        save_data()
        await update.message.reply_text('⏳ Ищем...')

async def stop_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in user_partners:
        partner_id = user_partners.pop(user_id, None)
        if partner_id and partner_id in user_partners:
            user_partners.pop(partner_id, None)
            save_data()
            await context.bot.send_message(partner_id, '❌ Партнер вышел')
        await update.message.reply_text('❌ Чат завершен')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    
    if user_id == ADMIN_ID:
        if text == '/stats':
            load_data()
            active = len([p for p in user_partners.values() if p is not None])
            await update.message.reply_text(f'📊 Чатов: {active//2}, Сообщений: {len(admin_messages)}')
        return
    
    load_data()
    partner_id = user_partners.get(user_id)
    if not partner_id:
        await update.message.reply_text('Сначала /find')
        return
    
    await context.bot.send_message(partner_id, f'👤 Аноним: {text}')
    msg = await context.bot.send_message(ADMIN_ID, f'👤{user_id}→👤{partner_id}: {text}')
    admin_messages[msg.message_id] = {'from': user_id, 'to': partner_id}
    save_data()

def main():
    load_data()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("find", find_partner))
    app.add_handler(CommandHandler("stop", stop_chat))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🚀 Бот запущен!")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
