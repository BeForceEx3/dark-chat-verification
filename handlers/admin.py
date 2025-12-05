from telegram import Update
from telegram.ext import ContextTypes
from utils.storage import load_data
from config import DATA_PATH

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    
    if user_id == ADMIN_ID:
        # Админ-команды
        if text.startswith('/stats'):
            partners, messages = load_data(DATA_PATH)
            active_chats = len([p for p in partners.values() if p is not None])
            await update.message.reply_text(f'📊 Статистика:\nАктивных чатов: {active_chats}\nСообщений: {len(messages)}')
        return
    
    # Обычные сообщения - анонимный чат
    reload_data()
    partner_id = user_partners.get(user_id)
    
    if not partner_id:
        await update.message.reply_text('Сначала найдите партнера: /find')
        return
    
    # Отправляем партнеру анонимно
    await context.bot.send_message(partner_id, f'👤 Аноним: {text}')
    
    # Логируем админу
    msg = await context.bot.send_message(
        ADMIN_ID, 
        f'👤{user_id} → 👤{partner_id}: {text}'
    )
    admin_messages[msg.message_id] = {'from_user': user_id, 'to_user': partner_id}
    save_data(DATA_PATH, user_partners, admin_messages)
