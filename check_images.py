import os
import logging
import tkinter as tk
from tkinter import filedialog
from google.cloud import storage
from datetime import timedelta

# ✅ Set your Google Cloud Storage bucket name
BUCKET_NAME = "telegram_bot_images_tamir"
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gcloud_key.json"

# ==============================
# 📌 Upload Image to Google Cloud
# ==============================
def upload_image_to_gcs(local_file_path: str, destination_blob_name: str) -> str:
    """
    Uploads an image to Google Cloud Storage and generates a signed URL.
    :param local_file_path: Path to the image file on the local machine.
    :param destination_blob_name: Name to save the file as in the bucket (same as filename).
    :return: Signed URL of the uploaded image (valid for 1 hour).
    """
    try:
        # ✅ Initialize the Google Cloud Storage client
        storage_client = storage.Client()
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(destination_blob_name)

        # ✅ Upload the image
        blob.upload_from_filename(local_file_path)

        # ✅ Generate a signed URL (valid for 1 hour)
        signed_url = blob.generate_signed_url(expiration=timedelta(hours=1))

        logging.info(f"✅ Image uploaded successfully: {signed_url}")
        return signed_url
    except Exception as e:
        logging.error(f"❌ Failed to upload image: {e}")
        return None

# ==============================
# 📌 Select Image via File Dialog
# ==============================
def select_image():
    """
    Opens a file dialog to select an image from the local computer.
    :return: Path of the selected image.
    """
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    file_path = filedialog.askopenfilename(
        title="Select an image to upload",
        filetypes=[("Image Files", "*.jpg;*.jpeg;*.png;*.gif;*.bmp")]
    )
    return file_path

# ==============================
# 📌 Main Execution
# ==============================
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("📂 Please select an image to upload...")
    local_image = select_image()

    if not local_image:
        print("❌ No image selected. Exiting...")
    else:
        destination_name = os.path.basename(local_image)  # 🔹 Store file in bucket root
        uploaded_url = upload_image_to_gcs(local_image, destination_name)

        if uploaded_url:
            print(f"✅ Image uploaded successfully: {uploaded_url}")
        else:
            print("❌ Image upload failed.")
