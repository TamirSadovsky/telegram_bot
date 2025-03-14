import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from handlers import start, handle_message
from config import TOKEN

# Log declarations
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO  
)

def create_app():  # ✅ Gunicorn can now call this function
    """Create and return a Telegram bot application instance."""
    logging.info("🚀 Creating Telegram bot application...")  

    app = Application.builder().token(TOKEN).build()

    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))  
    app.add_handler(MessageHandler(filters.PHOTO, handle_message))  

    return app  # ✅ Gunicorn now has a callable app function

if __name__ == "__main__":
    app = create_app()
    logging.info("📡 Bot is now running and listening for messages...") 
    app.run_polling()
