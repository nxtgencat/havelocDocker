import logging
import os

import dotenv
import requests

dotenv.load_dotenv()

# Global variables for Telegram bot
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN") # Replace with your actual bot token
BASE_URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"


def send_message_bot(chat_id, message):
    logging.info(f"Sending message to chat_id {chat_id}: {message}")

    payload = {
        "chat_id": chat_id,
        "text": message
    }

    try:
        response = requests.post(BASE_URL, data=payload)
        if response.status_code == 200:
            logging.info(f"Message sent successfully to {chat_id}")
        else:
            logging.error(f"Failed to send message to {chat_id}, Status Code: {response.status_code}")
    except Exception as e:
        logging.error(f"Error sending message to {chat_id}: {e}")
