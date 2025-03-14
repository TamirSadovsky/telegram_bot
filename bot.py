import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from handlers import start, handle_message
import os

TOKEN = os.environ.get("TOKEN")

# Log declarations
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO  
)

def create_app():
    """Create and return a WSGI application for Gunicorn."""

    logging.info("🚀 Creating Telegram bot application...")  

    app = Application.builder().token(TOKEN).build()

    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))  
    app.add_handler(MessageHandler(filters.PHOTO, handle_message))  

    logging.info("✅ Application setup completed.")  

    # ✅ Define a WSGI response function
    def wsgi_app(environ, start_response):
        """Minimal WSGI application to prevent Gunicorn crashes."""
        start_response('200 OK', [('Content-Type', 'text/plain')])
        return [b"Bot is running!"]

    return wsgi_app  # ✅ Now Gunicorn gets a valid WSGI app

# ✅ Keep the bot running when executed directly
if __name__ == "__main__":
    bot_app = create_app()
    logging.info("📡 Bot is now running and listening for messages...") 
    bot_app.run_polling()
