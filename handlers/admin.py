from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from config import ADMIN_ID, DATA_PATH
from handlers.chat import user_partners, reload_data
from utils.storage import load_data, save_data

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    
    if user_id != ADMIN_ID:
        _, messages = load_data(DATA_PATH)
        partner_id = user_partners.get(user_id)
        if not partner_id:
            await update.message.reply_text('❗ <b>Сначала найдите партнёра: /find</b>', parse_mode='HTML')
            return
        
        await context.bot.send_message(partner_id, f'👤 <b>Аноним:</b> {text}', parse_mode='HTML')
        
        # Лог админу
        msg = await context.bot.send_message(
            ADMIN_ID, f'👤de>{user_id}</code> → 👤de>{partner_id}</code>: {text}', 
            parse_mode='HTML'
        )
        messages[msg.message_id] = {'from': user_id, 'to': partner_id}
        save_data(DATA_PATH, user_partners, messages)
        return
    
    # Админ команды
    if text == '/stats':
        reload_data()
        active_chats = len([p for p in user_partners.values() if p is not None]) // 2
        waiting = len([p for p in user_partners.values() if p is None])
        keyboard = [[InlineKeyboardButton("🔄 Обновить", callback_data='stats')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f'📊 <b>Статистика:</b>\n\n'
            f'🔗 Активных чатов: de>{active_chats}</code>\n'
            f'⏳ В очереди: de>{waiting}</code>\n'
            f'💬 Сообщений: de>{len(messages)}</code>', 
            parse_mode='HTML', reply_markup=reply_markup)

async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'stats':
        reload_data()
        active_chats = len([p for p in user_partners.values() if p is not None]) // 2
        waiting = len([p for p in user_partners.values() if p is None])
        await query.edit_message_text(
            f'📊 <b>Статистика:</b>\n\n'
            f'🔗 Активных чатов: de>{active_chats}</code>\n'
            f'⏳ В очереди: de>{waiting}</code>\n'
            f'💬 Сообщений: de>{len(messages)}</code>', 
            parse_mode='HTML'
        )
