from telegram import Update
from telegram.ext import CallbackContext
import logging
from database import query_database
from states import *
import re
from validators import is_valid_israeli_phone, is_valid_hebrew_name, is_valid_mileage
import datetime
from datetime import datetime
import urllib.parse
import requests
import logging

GOOGLE_MAPS_API_KEY = "AIzaSyAWODnL_x9dbeoVV5vH0uVY7XIAjpfqZR0"  # 🔹 Replace with your API key

def get_best_location(query):
    """
    Searches Google Maps API to get the best possible location based on a pancheria name or address.
    """
    base_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {
        "query": query,
        "key": GOOGLE_MAPS_API_KEY
    }

    try:
        response = requests.get(base_url, params=params)
        data = response.json()

        if data["status"] == "OK":
            best_result = data["results"][0]["formatted_address"]
            return best_result
        else:
            logging.warning(f"⚠️ Google Maps API returned no results for query: {query}")
            return query  # Fallback to original query if no results found

    except Exception as e:
        logging.error(f"❌ Error fetching location from Google Maps API: {e}")
        return query  # Fallback in case of API failure

def generate_navigation_links(tire_shop_name):
    """ Generates Google Maps and Waze navigation links using the best possible query """

    # ✅ Clean and format the name
    formatted_name = urllib.parse.quote(tire_shop_name)

    # ✅ Try extracting an address from the name
    if "(" in tire_shop_name and ")" in tire_shop_name:
        extracted_address = tire_shop_name.split("(")[-1].replace(")", "").strip()
    elif "-" in tire_shop_name:
        extracted_address = tire_shop_name.split("-")[-1].strip()
    else:
        extracted_address = None

    # ✅ Use the best location available
    if extracted_address:
        best_location = get_best_location(extracted_address)  # Get precise location from Google
    else:
        best_location = get_best_location(tire_shop_name)  # Try searching the shop name

    # ✅ URL encode for maps & waze
    query = urllib.parse.quote(best_location)

    # ✅ Generate the links
    google_maps_link = f"https://www.google.com/maps/search/?api=1&query={query}"
    waze_link = f"https://waze.com/ul?q={query}"

    return google_maps_link, waze_link




async def start(update: Update, context: CallbackContext):
    logging.getLogger().setLevel(logging.INFO)
    """Start conversation and ask for car number."""
    user_id = update.message.chat_id
    user_states[user_id] = STATE_WAITING_FOR_CAR_NUMBER

    logging.info(f"👤 New user started the bot: {user_id}")

    message = (
        "<b>שלום נציג צה\"ל</b>\n\n"
        "תודה שבחרת לקבל שירות מ<b>צמיג רם</b> 🚗🔧\n\n"
        "⚠️ <b>לתשומת ליבך:</b> אם אתה צריך לפתוח קריאת שירות ליותר מכלי רכב אחד, "
        "סיים את הקריאה הנוכחית ופתח חדשה.\n\n"
        "✏️ <b>הקלד את מספר הרכב (ללא האות צ')</b>:"
    )

    await update.message.reply_text(message, parse_mode="HTML")
    logging.info(f"📨 Sent car number request to user {user_id}")

async def handle_message(update: Update, context: CallbackContext):
    """Handle user responses based on their state."""
    user_id = update.message.chat_id
    user_message = update.message.text

    if user_id not in user_states:
        await update.message.reply_text("⚠️ שלב לא מזוהה, נא להתחיל מחדש עם /start")
        logging.warning(f"⚠️ Unknown state for user {user_id}, message: {user_message}")
        return

    current_state = user_states[user_id]
    logging.info(f"🔄 User {user_id} in state: {current_state} - Received: {user_message}")

    if current_state == STATE_WAITING_FOR_CAR_NUMBER:
        result = query_database("EXEC FindCarNumForBot ?", (user_message,))
        if result:
            car_data = result[0]  # Assuming first row contains the relevant data

            # ✅ Dynamically filter out `None` values
            car_details = [str(car_data[i]) for i in [4, 7] if car_data[i] is not None]

            # ✅ Construct message only with existing values
            car_info_text = " - ".join(car_details) if car_details else "פרטים לא זמינים"

            user_states[user_id] = STATE_WAITING_FOR_CONFIRMATION
            await update.message.reply_text(
                f"✅ כלי הרכב אומת: {car_info_text}\n"
                "האם לאשר? (כן/לא)", parse_mode="HTML"
            )
            logging.info(f"✅ Car verified for user {user_id}: {car_info_text}")
        else:
            await update.message.reply_text("❌ כלי רכב זה אינו מופיע במערכת.")
            logging.warning(f"❌ Car verification failed for user {user_id}: {user_message}")

    elif current_state == STATE_WAITING_FOR_CONFIRMATION:
        if user_message.lower() == "כן":
            user_states[user_id] = STATE_WAITING_FOR_DRIVER_DETAILS
            await update.message.reply_text("👤 אנא הקלד את שם הנהג:")
        elif user_message.lower() == "לא":
            await update.message.reply_text("❌ קריאה בוטלה.")
            user_states.pop(user_id)
        else:
            await update.message.reply_text("⚠️ נא להזין 'כן' או 'לא' בלבד.")


    elif current_state == STATE_WAITING_FOR_DRIVER_DETAILS:
        # ✅ בדיקת שם חוקי בעברית בלבד
        if not await is_valid_hebrew_name(user_message):
            await update.message.reply_text("❌ שם הנהג לא תקין. יש להזין שם המכיל רק אותיות בעברית.")
            logging.warning(f"⚠️ Invalid driver name from user {user_id}: {user_message}")
            return

        context.user_data["driver_name"] = user_message  # שמירת השם התקין
        user_states[user_id] = STATE_WAITING_FOR_SERVICE_SELECTION
        await update.message.reply_text("📞 הקלד מספר טלפון של הנהג:")



    elif current_state == STATE_WAITING_FOR_SERVICE_SELECTION:
        # ✅ Validate phone number before proceeding
        if not await is_valid_israeli_phone(user_message):
            await update.message.reply_text("❌ מספר טלפון לא תקין. נא להזין מספר תקין בפורמט ישראלי ללא מקפים (למשל: 0521234567).")
            logging.warning(f"⚠️ Invalid phone number from user {user_id}: {user_message}")
            return

        context.user_data["driver_phone"] = user_message  # Store validated phone number

        # ✅ Fetch available services
        services = query_database("EXEC FindWorks")

        if services:
            valid_service_ids = {str(row[0]): row[1] for row in services if row[0] < 11}  # ✅ Store as a dictionary (ID -> Service Name)
            services_text = "\n".join([f"{row[0]} - {row[1]}" for row in services if row[0] < 11])
            user_states[user_id] = STATE_WAITING_FOR_TIRE_DETAILS

            await update.message.reply_text(
                f"🔧 אילו שירותים תרצה לבצע?\n{services_text}\n\n💡 יש להקליד רק את המספרים מהרשימה למעלה."
            )
            context.user_data["valid_service_ids"] = valid_service_ids  # Store valid service numbers
        else:
            await update.message.reply_text("❌ לא נמצאו שירותים זמינים.")

    elif current_state == STATE_WAITING_FOR_TIRE_DETAILS:
        valid_service_ids = context.user_data.get("valid_service_ids", {})  # Retrieve valid service IDs as a dictionary

        if user_message in valid_service_ids:
            service_name = valid_service_ids[user_message]  # ✅ Retrieve service name from the dictionary
            context.user_data["selected_service"] = service_name  # Store the service for reference

            if service_name.startswith("צמיג"):  # ✅ Check if the service is related to tires
                user_states[user_id] = STATE_WAITING_FOR_TIRE_QUANTITY
                await update.message.reply_text("🔢 כמה צמיגים תרצה להחליף? (1-20)")
                logging.info(f"🔍 User {user_id} selected tire service: {service_name}")
            else:
                user_states[user_id] = STATE_WAITING_FOR_MILEAGE
                await update.message.reply_text("📏 הקלד את מספר הק״מ של הרכב:")
                logging.info(f"🔍 User {user_id} selected non-tire service: {service_name}")
        else:
            await update.message.reply_text("❌ הבחירה שלך אינה תקפה. אנא הקלד מספר מתוך הרשימה שהוצגה.")
            logging.warning(f"⚠️ Invalid service selection from user {user_id}: {user_message}")

    elif current_state == STATE_WAITING_FOR_TIRE_QUANTITY:
        if not user_message.isdigit():
            await update.message.reply_text("❌ יש להזין מספר תקין בלבד (1-20).")
            logging.warning(f"⚠️ Invalid tire quantity from user {user_id}: {user_message}")
            return

        tire_quantity = int(user_message)

        if tire_quantity < 1 or tire_quantity > 20:
            await update.message.reply_text("❌ כמות אינה מאושרת. ניתן להזין מספר בין 1 ל-20 בלבד.")
            logging.warning(f"⚠️ User {user_id} entered an invalid tire quantity: {tire_quantity}")
            return

        context.user_data["tire_quantity"] = tire_quantity
        user_states[user_id] = STATE_WAITING_FOR_TIRE_POSITION  # ✅ Move to next step
        await update.message.reply_text("🚗 איפה נמצא הצמיג? \n1️⃣ - קדמי \n2️⃣ - אחורי")
        logging.info(f"✅ User {user_id} entered tire quantity: {tire_quantity}, asking for tire position.")

    elif current_state == STATE_WAITING_FOR_TIRE_POSITION:
        if user_message not in ["1", "2"]:
            await update.message.reply_text("❌ בחירה לא חוקית. יש לבחור: \n1️⃣ - קדמי \n2️⃣ - אחורי")
            logging.warning(f"⚠️ Invalid tire position selection from user {user_id}: {user_message}")
            return

        context.user_data["tire_position"] = "קדמי" if user_message == "1" else "אחורי"
        user_states[user_id] = STATE_WAITING_FOR_AXLE_POSITION  # ✅ Move to next step
        await update.message.reply_text("🔧 איפה הצמיג על הסרן? \n1️⃣ - פנימי \n2️⃣ - חיצוני")
        logging.info(f"✅ User {user_id} selected tire position: {context.user_data['tire_position']}, asking for axle position.")

    elif current_state == STATE_WAITING_FOR_AXLE_POSITION:
        if user_message not in ["1", "2"]:
            await update.message.reply_text("❌ בחירה לא חוקית. יש לבחור: \n1️⃣ - פנימי \n2️⃣ - חיצוני")
            logging.warning(f"⚠️ Invalid axle position selection from user {user_id}: {user_message}")
            return

        context.user_data["axle_position"] = "פנימי" if user_message == "1" else "חיצוני"
        user_states[user_id] = STATE_WAITING_FOR_IMAGES  # ✅ Now move to image upload
        await update.message.reply_text("📸 שלח תמונה של הצמיגים להחלפה.")
        logging.info(f"✅ User {user_id} selected axle position: {context.user_data['axle_position']}, proceeding to image upload.")

    elif current_state == STATE_WAITING_FOR_IMAGES:
        user_states[user_id] = STATE_WAITING_FOR_MILEAGE  # ✅ Now ask for mileage after all צמיגים questions
        await update.message.reply_text("📏 הקלד את מספר הק״מ של הרכב (ספרות בלבד).")

    elif current_state == STATE_WAITING_FOR_MILEAGE:
        # ✅ Allow numbers with up to two decimal places (e.g., 10.5, 123.45)
        if not is_valid_mileage(user_message):
            await update.message.reply_text("❌ יש להזין מספר תקין (לדוגמה: 123 או 123.45).")
            logging.warning(f"⚠️ Invalid mileage input from user {user_id}: {user_message}")
            return

        context.user_data["mileage"] = float(user_message)  # Convert to float before storing
        user_states[user_id] = STATE_WAITING_FOR_AREA

# ✅ Fetch available areas and store them properly
        areas = query_database("EXEC FindArea")
        if areas:
            valid_area_ids = {str(row[0]): row[1] for row in areas}  # Store {AreaID: AreaName}
            context.user_data["valid_area_ids"] = valid_area_ids  # Save for later validation

            areas_text = "\n".join([f"{row[0]} - {row[1]}" for row in areas])
            await update.message.reply_text(f"📍 באיזה אזור אתה רוצה שירות?\n{areas_text}")
        else:
            await update.message.reply_text("❌ לא נמצאו אזורים זמינים.")

    elif current_state == STATE_WAITING_FOR_AREA:
        valid_area_ids = context.user_data.get("valid_area_ids", {})  # Retrieve stored areas

        if user_message in valid_area_ids:  # ✅ Correctly checking against stored areas
            area_name = valid_area_ids[user_message]  # Retrieve area name
            context.user_data["area"] = area_name  # Store selected area

            # ✅ Log correct area name
            logging.info(f"🔍 User {user_id} searching for tire shops in: {area_name}")

            # ✅ Execute query with AreaDes instead of AreaID
            tire_shops = query_database("EXEC FindPancheria ?", (area_name,))

            if tire_shops:
                # ✅ Store valid tire shop IDs in context
                valid_tire_shop_ids = {str(row[0]): row[1] for row in tire_shops}  # Dictionary {BranchID: Name}
                context.user_data["valid_tire_shop_ids"] = valid_tire_shop_ids

                # ✅ Format results properly
                tire_shops_text = "\n".join([f"{row[0]} - {row[1]} ({row[6]})" for row in tire_shops])  # BranchID - Name (Address)
                user_states[user_id] = STATE_WAITING_FOR_TIRE_SHOP

                await update.message.reply_text(
                    f"🏪 פנצריות זמינות באזור {area_name}:\n{tire_shops_text}\n\nאנא בחר מספר פנצריה."
                )
                logging.info(f"✅ Found {len(tire_shops)} tire shops in {area_name}.")
            else:
                await update.message.reply_text("❌ לא נמצאו פנצריות באזור זה. נסה אזור אחר.")
                logging.warning(f"⚠️ No tire shops found for {area_name}.")
        else:
            await update.message.reply_text("❌ הבחירה שלך אינה תקפה. אנא הקלד מספר מתוך הרשימה.")
            logging.warning(f"⚠️ Invalid area selection from user {user_id}: {user_message}")


    elif current_state == STATE_WAITING_FOR_TIRE_SHOP:
        valid_tire_shop_ids = context.user_data.get("valid_tire_shop_ids", {})

        if user_message in valid_tire_shop_ids:
            selected_tire_shop = valid_tire_shop_ids[user_message]  # Get the tire shop name
            context.user_data["selected_tire_shop"] = selected_tire_shop

            # ✅ Ask for a date before sending navigation links
            user_states[user_id] = STATE_WAITING_FOR_DATE
            await update.message.reply_text("📅 אנא הזן תאריך לפגישה (יום-חודש-שנה), למשל: 07-03-2025")
            logging.info(f"✅ User {user_id} selected tire shop: {selected_tire_shop}, asking for appointment date.")

        else:
            await update.message.reply_text("❌ הבחירה שלך אינה תקפה. אנא הקלד מספר פנצריה מתוך הרשימה.")
            logging.warning(f"⚠️ Invalid tire shop selection from user {user_id}: {user_message}")

    elif current_state == STATE_WAITING_FOR_DATE:
        try:
            # ✅ Log raw input for debugging
            logging.info(f"📅 Raw user input for date: '{user_message}' (length: {len(user_message)})")

            # ✅ Remove unexpected characters and decimals
            import re
            clean_date = re.sub(r"[^\d-]", "", user_message.strip().split(".")[0])

            # ✅ Parse the date explicitly as DD-MM-YYYY
            selected_date = datetime.strptime(clean_date, "%d-%m-%Y").date()

            today = datetime.today().date()

            if selected_date < today:
                await update.message.reply_text("❌ התאריך אינו חוקי. אנא הזן תאריך עתידי (למשל: 07-03-2025).")
                logging.warning(f"⚠️ Invalid past date from user {user_id}: {selected_date}")
                return

            context.user_data["selected_date"] = selected_date
            branch_name = context.user_data["selected_tire_shop"].strip()

            # ✅ Fetch Branch ID (ensure we have the correct pancheria)
            branch_id_result = query_database("SELECT BranchID FROM dbo.Branchs WHERE RTRIM(LTRIM(Name)) = ?", (branch_name,))

            if not branch_id_result:
                await update.message.reply_text("❌ שגיאה: לא נמצא מזהה פנצריה מתאים.")
                logging.error(f"❌ Branch ID not found for: {branch_name}")
                return

            branch_id = branch_id_result[0][0]  # Extract the integer BranchID

            # ✅ Convert date to SQL format ("YYYY-MM-DD")
            selected_date_str = selected_date.strftime("%Y-%m-%d")

            # ✅ Fetch available times using the stored procedure (now filters by date AND pancheria)
            available_times = query_database("EXEC [dbo].[FindTmpTime] ?, ?", (selected_date_str, branch_id))

            if available_times:
                # ✅ Convert times to HH:MM and store them in a dictionary with a numeric choice
                formatted_times = [datetime.strptime(row[0].split(".")[0], "%H:%M:%S").strftime("%H:%M") for row in available_times]
                time_choices = {str(i + 1): formatted_times[i] for i in range(len(formatted_times))}

                # ✅ Format the message with numbers (RTL for Hebrew)
                times_text = "\n".join([f"{time} - {i+1}" for i, time in enumerate(formatted_times)])

                # ✅ Store the mapping so we can validate user input
                context.user_data["available_times"] = time_choices

                user_states[user_id] = STATE_WAITING_FOR_TIME
                await update.message.reply_text(f"⏰ זמני פגישה זמינים ל-{clean_date}:\n{times_text}\n\n🔹 אנא בחר מספר מהרשימה.")
            else:
                await update.message.reply_text("❌ לא נמצאו זמני פגישה זמינים בתאריך זה. נסה תאריך אחר.")
                logging.warning(f"⚠️ No available times for user {user_id} on {selected_date}.")
        except ValueError as e:
            await update.message.reply_text("❌ פורמט תאריך לא תקין. נא להזין תאריך בפורמט יום-חודש-שנה (למשל: 07-03-2025).")
            logging.error(f"❌ Date parsing error for user {user_id}: {user_message} | Error: {e}")


    elif current_state == STATE_WAITING_FOR_TIME:
        available_times = context.user_data.get("available_times", {})

        if user_message in available_times:
            selected_time = available_times[user_message]
            context.user_data["selected_time"] = selected_time  # Store selected time

            # ✅ Get the pancheria name
            tire_shop_name = context.user_data["selected_tire_shop"]

            # ✅ Generate accurate navigation links
            google_maps_link, waze_link = generate_navigation_links(tire_shop_name)

            # ✅ Convert the selected date back to DD-MM-YYYY format
            selected_date_str = context.user_data["selected_date"].strftime("%d-%m-%Y")

            # ✅ Now send the navigation links
            await update.message.reply_text(
                f"✅ הפגישה נקבעה בהצלחה!\n📅 תאריך: {selected_date_str}\n⏰ שעה: {selected_time}\n🏪 פנצריה: {tire_shop_name}\n\n"
                f"🔗 [לחץ כאן לניווט עם Google Maps]({google_maps_link})\n"
                f"🔗 [לחץ כאן לניווט עם Waze]({waze_link})",
                parse_mode="Markdown"
            )

            logging.info(f"✅ User {user_id} booked appointment on {selected_date_str} at {selected_time}")
            user_states.pop(user_id)  # Clear state after completion
        else:
            await update.message.reply_text("❌ המספר שנבחר אינו תקף. אנא בחר מספר מהרשימה.")
            logging.warning(f"⚠️ Invalid time selection from user {user_id}: {user_message}")







    
    


    elif current_state == STATE_WAITING_FOR_APPOINTMENT:
        await update.message.reply_text("✅ בקשתך נקלטה!")

