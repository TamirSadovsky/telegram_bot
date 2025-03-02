from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, CallbackContext
import pyodbc  # For SQL Server connection
import logging

TOKEN = "7724271405:AAHVY_uYfvSEbyCMD71N-OHSUGdEyqhZ5po"

# SQL Server connection details
DB_CONNECTION_STRING = "DRIVER={SQL Server};SERVER=81.218.80.23\\WIZSOFT,7002;DATABASE=Ram;UID=sa;PWD=wizsoft"

# Dictionary to track user states
user_states = {}

# Constants for state management
STATE_WAITING_FOR_CAR_NUMBER = "waiting_for_car_number"
STATE_WAITING_FOR_CONFIRMATION = "waiting_for_confirmation"
STATE_WAITING_FOR_DRIVER_DETAILS = "waiting_for_driver_details"
STATE_WAITING_FOR_SERVICE_SELECTION = "waiting_for_service_selection"
STATE_WAITING_FOR_TIRE_DETAILS = "waiting_for_tire_details"
STATE_WAITING_FOR_TIRE_QUANTITY = "waiting_for_tire_quantity"
STATE_WAITING_FOR_IMAGES = "waiting_for_images"
STATE_WAITING_FOR_MILEAGE = "waiting_for_mileage"
STATE_WAITING_FOR_AREA = "waiting_for_area"
STATE_WAITING_FOR_TIRE_SHOP = "waiting_for_tire_shop"
STATE_WAITING_FOR_APPOINTMENT = "waiting_for_appointment"

# Enable logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)


# ✅ Connect to SQL Server & Execute Queries
def query_database(query, params=None):
    """Execute a query and return results"""
    try:
        with pyodbc.connect(DB_CONNECTION_STRING) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params if params else ())
            print("✅ Query Executed Successfully!")
            return cursor.fetchall()
    except Exception as e:
        print(f"❌ Database error: {e}")
        return None


# ✅ Start Command
async def start(update: Update, context: CallbackContext):
    """Start conversation and ask for car number."""
    user_id = update.message.chat_id
    user_states[user_id] = STATE_WAITING_FOR_CAR_NUMBER

    message = (
        "<b>שלום נציג צה\"ל</b>\n\n"
        "תודה שבחרת לקבל שירות מ<b>צמיג רם</b> 🚗🔧\n\n"
        "⚠️ <b>לתשומת ליבך:</b> אם אתה צריך לפתוח קריאת שירות ליותר מכלי רכב אחד, "
        "סיים את הקריאה הנוכחית ופתח חדשה.\n\n"
        "✏️ <b>הקלד את מספר הרכב (ללא האות צ')</b>:"
    )

    await update.message.reply_text(message, parse_mode="HTML")


# ✅ Handling User Messages
async def handle_message(update: Update, context: CallbackContext):
    """Handle user responses based on their state."""
    user_id = update.message.chat_id
    user_message = update.message.text

    if user_id not in user_states:
        await update.message.reply_text("⚠️ שלב לא מזוהה, נא להתחיל מחדש עם /start")
        return

    current_state = user_states[user_id]

    if current_state == STATE_WAITING_FOR_CAR_NUMBER:
        # Validate car number with SQL
        result = query_database("EXEC FindCarNumForBot ?", (user_message,))
        if result:
            user_states[user_id] = STATE_WAITING_FOR_CONFIRMATION
            await update.message.reply_text(
                f"✅ כלי הרכב אומת: {result[0][4]} - {result[0][7]}\n"
                "האם לאשר? (כן/לא)", parse_mode="HTML"
            )
        else:
            await update.message.reply_text("❌ כלי רכב זה אינו מופיע במערכת. פנה לקצין הרכב להוספה.")

    elif current_state == STATE_WAITING_FOR_CONFIRMATION:
        if user_message.lower() == "כן":
            user_states[user_id] = STATE_WAITING_FOR_DRIVER_DETAILS
            await update.message.reply_text("👤 אנא הקלד את שם הנהג:")
        else:
            await update.message.reply_text("❌ קריאה בוטלה.")
            user_states.pop(user_id)

    elif current_state == STATE_WAITING_FOR_DRIVER_DETAILS:
        context.user_data["driver_name"] = user_message
        user_states[user_id] = STATE_WAITING_FOR_SERVICE_SELECTION
        await update.message.reply_text("📞 הקלד מספר טלפון של הנהג:")

    elif current_state == STATE_WAITING_FOR_SERVICE_SELECTION:
        context.user_data["driver_phone"] = user_message
        
        # ✅ Get the list of services from SQL
        services = query_database("EXEC FindWorks")
        
        if services:
            services_text = "\n".join([f"{row[0]} - {row[1]}" for row in services if row[0] < 11])  # ✅ Only GroupId < 11
            user_states[user_id] = STATE_WAITING_FOR_TIRE_DETAILS
            await update.message.reply_text(f"🔧 אילו שירותים תרצה לבצע?\n{services_text}\n\nשלח את מספר השירות הרצוי.")
        else:
            await update.message.reply_text("❌ לא נמצאו שירותים זמינים.")

    elif current_state == STATE_WAITING_FOR_TIRE_DETAILS:
        # ✅ Check if user selected "Tires" (assuming GroupId 1 is for tires)
        if user_message == "1":  
            user_states[user_id] = STATE_WAITING_FOR_TIRE_QUANTITY
            await update.message.reply_text("🔢 כמה צמיגים תרצה להחליף?")
        else:
            user_states[user_id] = STATE_WAITING_FOR_IMAGES
            await update.message.reply_text("📸 שלח תמונה של הצמיגים להחלפה.")

    elif current_state == STATE_WAITING_FOR_TIRE_QUANTITY:
        context.user_data["tire_quantity"] = user_message
        user_states[user_id] = STATE_WAITING_FOR_IMAGES
        await update.message.reply_text("📸 שלח תמונה של הצמיגים להחלפה.")

    elif current_state == STATE_WAITING_FOR_IMAGES:
        user_states[user_id] = STATE_WAITING_FOR_MILEAGE
        await update.message.reply_text("📏 הקלד את מספר הק״מ של הרכב:")

    elif current_state == STATE_WAITING_FOR_MILEAGE:
        context.user_data["mileage"] = user_message
        areas = query_database("EXEC FindArea")
        areas_text = "\n".join([f"{row[0]} - {row[1]}" for row in areas])
        user_states[user_id] = STATE_WAITING_FOR_AREA
        await update.message.reply_text(f"📍 באיזה אזור אתה רוצה שירות?\n{areas_text}")

    elif current_state == STATE_WAITING_FOR_AREA:
        context.user_data["area"] = user_message
        user_states[user_id] = STATE_WAITING_FOR_TIRE_SHOP
        await update.message.reply_text("🏪 בחר פנצריה מהרשימה.")

    elif current_state == STATE_WAITING_FOR_TIRE_SHOP:
        user_states[user_id] = STATE_WAITING_FOR_APPOINTMENT
        await update.message.reply_text("📅 בחר תאריך ושעה.")

    elif current_state == STATE_WAITING_FOR_APPOINTMENT:
        await update.message.reply_text("✅ בקשתך נקלטה!")


# ✅ Start the Telegram Bot
def main():
    """Start the bot"""
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()


# ✅ Run the Bot
if __name__ == "__main__":
    main()
