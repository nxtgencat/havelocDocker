import base64
import json
import logging
import os
import dotenv

dotenv.load_dotenv()

def decrypt_base64(encoded_data):
    try:
        logging.info("Starting decryption of base64 encoded data.")
        # Decode the Base64 encoded data
        decrypted_data = base64.b64decode(encoded_data)
        # Convert bytes to string for better readability (if it contains text data)
        logging.info("Decryption successful.")
        return decrypted_data.decode('utf-8', errors='ignore')
    except Exception as e:
        logging.error(f"An error occurred during decryption: {e}")
        return f"An error occurred during decryption: {e}"


def get_haveloc_credentials():
    try:
        logging.info("Attempting to read credentials from environment variable")
        # Get the base64 encoded string from environment variable
        encoded_credentials = os.getenv('HAVELOC_CREDENTIALS')

        if not encoded_credentials:
            logging.error("HAVELOC_CREDENTIALS environment variable not found")
            raise ValueError("HAVELOC_CREDENTIALS environment variable is not set")

        # Decode and parse the credentials
        decoded_data = decrypt_base64(encoded_credentials)
        json_data = json.loads(decoded_data)
        logging.info("Successfully parsed credentials JSON.")
        # print(json_data)
        return json_data

    except Exception as e:
        logging.error(f"An error occurred while processing credentials: {e}")
        raise

# get_haveloc_credentials()