import base64
import json
import requests
import logging


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
    # URL of the raw file on GitHub
    url = "https://raw.githubusercontent.com/nxtgencat/HavelocScraper/refs/heads/master/havcred"

    try:
        logging.info(f"Sending GET request to {url}")
        # Sending a GET request to fetch the raw data
        response = requests.get(url)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            logging.info("Credentials fetched successfully.")
            # Getting the content of the response
            raw_data = response.text
            decoded_data = decrypt_base64(raw_data)
            json_data = json.loads(decoded_data)
            logging.info("Successfully parsed credentials JSON.")
            return json_data
        else:
            logging.error(f"Failed to fetch data. Status code: {response.status_code}")

    except Exception as e:
        logging.error(f"An error occurred: {e}")