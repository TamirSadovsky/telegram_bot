import os
import logging
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from google.cloud import storage
from datetime import timedelta

# ✅ Set your Telegram Bot Token
TELEGRAM_BOT_TOKEN = "7724271405:AAHVY_uYfvSEbyCMD71N-OHSUGdEyqhZ5po"


# ✅ Set your Google Cloud Storage bucket name
BUCKET_NAME = "telegram_bot_images_tamir"
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gcloud_key.json"

# ✅ Initialize the Google Cloud Storage client
storage_client = storage.Client()
bucket = storage_client.bucket(BUCKET_NAME)

# ==========================
# 📌 Upload Image to GCS
# ==========================
def upload_image_to_gcs(local_file_path: str, destination_blob_name: str) -> str:
    """
    Uploads an image to Google Cloud Storage and returns a public URL.
    """
    try:
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_filename(local_file_path)

        # ✅ Make the file publicly accessible
        blob.make_public()

        public_url = blob.public_url
        logging.info(f"✅ Image uploaded successfully: {public_url}")
        return public_url
    except Exception as e:
        logging.error(f"❌ Failed to upload image: {e}")
        return None


# ==========================
# 📌 Handle Image Messages
# ==========================
async def handle_photo(update: Update, context: CallbackContext) -> None:
    """
    Receives an image from the user, downloads it, and uploads it to Google Cloud.
    """
    try:
        # ✅ Get the highest-resolution image
        photo = update.message.photo[-1]
        file_id = photo.file_id

        # ✅ Get the Telegram file info
        file_info = await context.bot.get_file(file_id)
        logging.info(f"📸 DEBUG: Received file_info: {file_info}")

        file_path = f"images/{file_id}.jpg"

        # ✅ Extract the correct file path
        correct_file_path = file_info.file_path.replace(f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/", "")

        # ✅ Construct the correct download URL
        download_url = f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{correct_file_path}"
        logging.info(f"🔍 DEBUG: Corrected download URL: {download_url}")

        # ✅ Download the file
        response = requests.get(download_url)
        if response.status_code == 200:
            with open(file_path, 'wb') as f:
                f.write(response.content)
            logging.info(f"✅ DEBUG: Image downloaded successfully: {file_path}")
        else:
            logging.error(f"❌ ERROR: Failed to download file. HTTP Status: {response.status_code}")
            await update.message.reply_text("❌ לא ניתן להוריד את התמונה.")
            return

        # ✅ Upload to Google Cloud Storage
        uploaded_url = upload_image_to_gcs(file_path, file_path)

        if uploaded_url:
            await update.message.reply_text(f"✅ התמונה הועלתה בהצלחה!\n🔗 {uploaded_url}")
        else:
            await update.message.reply_text("❌ כשל בהעלאת התמונה לענן.")

    except Exception as e:
        logging.error(f"❌ ERROR: {e}")
        await update.message.reply_text("❌ שגיאה כללית. נסה לשלוח את התמונה שוב.")


# ==========================
# 📌 Start Command
# ==========================
async def start(update: Update, context: CallbackContext) -> None:
    """
    Sends a welcome message when the bot starts.
    """
    await update.message.reply_text("👋 שלח תמונה ואני אעלה אותה לענן! 📤")

# ==========================
# 📌 Main Function
# ==========================
def main():
    print("✅ DEBUG: Script started.")  # 🔍 Check if the script runs at all

    logging.basicConfig(level=logging.INFO)

    # ✅ Initialize the bot
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # ✅ Register Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    # ✅ Start the bot
    logging.info("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
