import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from handlers import start, handle_message
from config import TOKEN
from image_handler import save_image
from telegram.ext import CallbackQueryHandler


# Log declarations
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO  
)

# ✅ Define the app instance globally so Gunicorn can find it
app = Application.builder().token(TOKEN).build()

# Add handlers
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))  # Handle text messages
app.add_handler(MessageHandler(filters.PHOTO, handle_message))  # Handle images separately

# ✅ Gunicorn expects an app object, so it needs to be a callable WSGI application
def run():
    """Start the bot"""
    logging.info("🚀 Starting Telegram bot...")
    logging.info("✅ Application created successfully!")  
    logging.info("📡 Bot is now running and listening for messages...") 

    app.run_polling()

# ✅ Gunicorn looks for 'app', so we assign 'app' to a function reference
if __name__ == "__main__":
    run()
