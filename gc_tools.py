from config import bucket, GOOGLE_MAPS_API_KEY
import logging, requests, urllib.parse


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
