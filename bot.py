import logging
import os
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler, 
    filters, ContextTypes
)
from config import BOT_TOKEN, ADMIN_ID, DATAPATH
import handlers.start, handlers.chat, handlers.admin

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.error(f"Update {update} caused error {context.error}")

def main():
    if not BOT_TOKEN:
        print("BOT_TOKEN не установлен!")
        return
    
    os.makedirs(os.path.dirname(DATAPATH), exist_ok=True)
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", handlers.start.start))
    app.add_handler(CommandHandler("find", handlers.chat.findpartner))
    app.add_handler(CommandHandler("stop", handlers.chat.stopchat))
    
    app.add_handler(CallbackQueryHandler(handlers.chat.findpartner, pattern="^find$"))
    app.add_handler(CallbackQueryHandler(handlers.chat.stopchat, pattern="^stop$"))
    app.add_handler(CallbackQueryHandler(handlers.admin.admin_callback, pattern="^stats$"))
    
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.admin.handlemessage))
    app.add_error_handler(error_handler)
    
    print("🚀 Бот запущен!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
