[translate:from telegram import Update]
[translate:from telegram.ext import ContextTypes]
[translate:from config import ADMIN_ID, DATA_PATH]  # ← ДОБАВЬТЕ ЭТУ СТРОКУ
[translate:from handlers.chat import user_partners, admin_messages, load_data, save_data]

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    
    if user_id == ADMIN_ID and text == '/stats':  # ← ТЕПЕРЬ РАБОТАЕТ
        load_data()
        active = len([p for p in user_partners.values() if p is not None]) // 2
        await update.message.reply_text(f'📊 Активных чатов: {active}\nСообщений: {len(admin_messages)}')
        return
    
    load_data()
    partner_id = user_partners.get(user_id)
    if not partner_id:
        await update.message.reply_text('❗ /find')
        return
    
    await context.bot.send_message(partner_id, f'👤 {text}')
    msg = await context.bot.send_message(ADMIN_ID, f'👤{user_id}→{partner_id}: {text}')
    admin_messages[msg.message_id] = {'from': user_id, 'to': partner_id}
    save_data()
