from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import logging

# Replace with your actual Telegram Bot Token
TOKEN = "7724271405:AAHVY_uYfvSEbyCMD71N-OHSUGdEyqhZ5po"  

# Enable logging for debugging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

async def start(update: Update, context: CallbackContext):
    """Handles the /start command with properly escaped MarkdownV2 formatting"""
    message = (
        "*שלום נציג צה\"ל*\n\n"
        "תודה שבחרת לקבל שירות מ*צמיגי רם* 🚗🔧\n\n"
        "⚠️ *לתשומת ליבך:* במידה ואת/ה צריכים לפתוח קריאת שירות ליותר מכלי רכב אחד, "
        "יש לסיים את קריאת השירות הנוכחית ולאחריה לפתוח קריאה חדשה\\.\n\n"
        "✏️ *נא להקליד את מספר ה\\-צ'* של כלי הרכב שעבורו תרצו לקבל שירות \\(ללא האות צ'\\):"
    )

    await update.message.reply_text(message, parse_mode="MarkdownV2")




def main():
    """Starts the bot using Application"""
    app = Application.builder().token(TOKEN).build()

    # Add command handlers
    app.add_handler(CommandHandler("start", start))

    # Run the bot
    app.run_polling()

if __name__ == "__main__":
    main()
