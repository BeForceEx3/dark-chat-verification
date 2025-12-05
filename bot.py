import logging
import os
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from config import BOT_TOKEN
import handlers.start, handlers.chat, handlers.admin

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def main():
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN не найден в переменных окружения!")
        return
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Команды
    app.add_handler(CommandHandler("start", handlers.start.start))
    app.add_handler(CommandHandler("find", handlers.chat.find_partner))
    app.add_handler(CommandHandler("stop", handlers.chat.stop_chat))
    
    # Callback кнопки
    app.add_handler(CallbackQueryHandler(handlers.chat.find_partner, pattern='^find$'))
    app.add_handler(CallbackQueryHandler(handlers.chat.stop_chat, pattern='^stop$'))
    app.add_handler(CallbackQueryHandler(handlers.admin.admin_callback, pattern='^(stats|reload)$'))
    
    # Сообщения
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.admin.handle_message))
    
    print("🚀 Бот запущен!")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
