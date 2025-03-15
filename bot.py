import logging
import threading
import asyncio
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
    """Create and return the Telegram bot application."""
    
    logging.info("🚀 Creating Telegram bot application...")  

    app = Application.builder().token(TOKEN).build()

    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))  
    app.add_handler(MessageHandler(filters.PHOTO, handle_message))  

    logging.info("✅ Application setup completed.")  

    return app

# ✅ Create the bot application
application = create_app()

# ✅ Define a WSGI function for Gunicorn
def wsgi_app(environ, start_response):
    """Minimal WSGI app for Gunicorn."""
    start_response('200 OK', [('Content-Type', 'text/plain')])
    return [b"Bot is running!"]

# ✅ Start polling in a separate thread
def start_polling():
    logging.info("📡 Bot is now running and listening for messages...") 
    asyncio.run(application.run_polling())

polling_thread = threading.Thread(target=start_polling, daemon=True)
polling_thread.start()
