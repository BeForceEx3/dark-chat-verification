from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import ADMINID, DATAPATH
from handlers.chat import userpartners, reloaddata
from utils.storage import loaddata, savedata

async def handlemessage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    userid = update.effective_user.id
    text = update.message.text
    
    if userid != ADMINID:
        return
    
    partners, messages = loaddata(DATAPATH)
    partnerid = userpartners.get(userid)
    
    if not partnerid:
        await update.message.reply_text("<b>find</b>", parse_mode='HTML')
        return
    
    await context.bot.send_message(partnerid, f"<b><b>{text}</b>", parse_mode='HTML')
    
    msg = await context.bot.send_message(
        ADMINID, 
        f"<code>de>{userid}</code> de>{partnerid}</code>\n{text}", 
        parse_mode='HTML'
    )
    messages[msg.message_id] = {"from": userid, "to": partnerid}
    savedata(DATAPATH, userpartners, messages)
    return

if text == "stats":
    reloaddata()
    partners, messages = loaddata(DATAPATH)  # Загружаем messages
    activechats = len([p for p in userpartners.values() if p is not None and p != 0]) // 2
    waiting = len([p for p in userpartners.values() if p is None])
    
    keyboard = [[InlineKeyboardButton("🔄", callback_data="stats")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"<b>👥 Активных чатов:</b> <code>{activechats}</code>\n"
        f"<b>⏳ В ожидании:</b> <code>{waiting}</code>\n"
        f"<b>💬 Сообщений:</b> <code>{len(messages)}</code>", 
        parse_mode='HTML', 
        reply_markup=reply_markup
    )

async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "stats":
        reloaddata()
        partners, messages = loaddata(DATAPATH)  # Загружаем messages
        activechats = len([p for p in userpartners.values() if p is not None and p != 0]) // 2
        waiting = len([p for p in userpartners.values() if p is None])
        
        await query.edit_message_text(
            f"<b>👥 Активных чатов:</b> <code>{activechats}</code>\n"
            f"<b>⏳ В ожидании:</b> <code>{waiting}</code>\n"
            f"<b>💬 Сообщений:</b> <code>{len(messages)}</code>", 
            parse_mode='HTML'
        )[file:1]
