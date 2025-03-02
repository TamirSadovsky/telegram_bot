import os
import logging
from telegram import Update
from telegram.ext import CallbackContext

# Path where images will be saved
IMAGE_SAVE_PATH = "images/"

# Ensure the folder exists
os.makedirs(IMAGE_SAVE_PATH, exist_ok=True)

async def save_image(update: Update, context: CallbackContext):
    """Handles saving images sent by users."""
    user_id = update.message.chat_id

    # Check if the user sent a photo
    if not update.message.photo:
        await update.message.reply_text("⚠️ נא לשלוח תמונה ולא קובץ אחר.")
        logging.warning(f"⚠️ User {user_id} attempted to send a non-photo file.")
        return

    photo = update.message.photo[-1]  # Get the highest resolution image
    file = await photo.get_file()
    
    # Define the file path
    file_path = os.path.join(IMAGE_SAVE_PATH, f"{user_id}_{file.file_id}.jpg")
    
    # Download and save the image
    await file.download(file_path)

    logging.info(f"✅ Image received and saved: {file_path} for user {user_id}")
    await update.message.reply_text("📸 התמונה נשמרה בהצלחה!")
