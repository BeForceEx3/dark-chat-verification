import logging
import os
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    CallbackQueryHandler, 
    filters,
    ContextTypes
)
from config import BOTTOKEN
import handlers.start
import handlers.chat
import handlers.admin

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Логирует ошибки без краша бота"""
    logging.error(f"Update {update} caused error {context.error}")

def main():
    if not BOTTOKEN:
        print("BOTTOKEN не установлен!")
        return
    
    app = Application.builder().token(BOTTOKEN).build()
    
    # Команды
    app.add_handler(CommandHandler("start", handlers.start.start))
    app.add_handler(CommandHandler("find", handlers.chat.findpartner))
    app.add_handler(CommandHandler("stop", handlers.chat.stopchat))
    
    # Callback handlers
    app.add_handler(CallbackQueryHandler(handlers.chat.findpartner, pattern="^find$"))
    app.add_handler(CallbackQueryHandler(handlers.chat.stopchat, pattern="^stop$"))
    app.add_handler(CallbackQueryHandler(handlers.admin.admin_callback, pattern="^stats$"))
    
    # Сообщения только для админа (текст без команд)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.admin.handlemessage))
    
    # Обработчик ошибок
    app.add_error_handler(error_handler)
    
    print("Бот запущен!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
