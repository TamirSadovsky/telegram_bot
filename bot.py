import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from handlers import start, handle_message
from config import TOKEN
from image_handler import save_image


# Log declarations
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO  
)

def main():
    """Start the bot"""
    logging.info("🚀 Starting Telegram bot...")  

    app = Application.builder().token(TOKEN).build()

    logging.info("✅ Application created successfully!")  

    # Add handlers
    app.add_handler(CommandHandler("start", start))
    

    logging.info("📡 Bot is now running and listening for messages...") 

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))  # Handle text messages
    app.add_handler(MessageHandler(filters.PHOTO, handle_message))  # Handle images separately



    app.run_polling()

if __name__ == "__main__":
    main()
