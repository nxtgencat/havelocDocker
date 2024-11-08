import requests
from supabase import create_client
import logging

# Global variables for Telegram bot
TOKEN = '8049997274:AAHfCdEdD-jCcw9ovmUgUDEYu7w7SJx8naY'  # Replace with your actual bot token
BASE_URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

# Supabase setup (ensure these are correct)
SUPABASE_URL = "https://zlygxmxwzigeuecbwukw.supabase.co"  # Your Supabase URL
SUPABASE_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpseWd4bXh3emlnZXVlY2J3dWt3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzA5MDY5MTAsImV4cCI6MjA0NjQ4MjkxMH0.ikIH_7vobQdWDz945ID17LLdRX8D5JCfut0_Z2P47sU"  # Your Supabase API key

# Initialize logging
logging.basicConfig(level=logging.INFO)

# Initialize Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_API_KEY)


def fetch_and_update_users(company_name: str, nxtresult: str):
    """
    Function to fetch all users from the 'users' table, check if their reg_number is in nxtresult,
    update their shortlisted_companies, and send a message.

    Args:
    nxtresult (str): A comma-separated string of registration numbers.
    company_name (str): The name of the company to be added to shortlisted_companies.
    """
    # Split nxtresult into a list of registration numbers
    reg_numbers = nxtresult.split(',')

    # Fetch all users from the 'users' table
    logging.info("Fetching users from the database...")
    users = supabase.table("users").select("*").execute()

    logging.info(f"Fetched {len(users.data)} users from the database.")

    for user in users.data:
        chat_id = user["chat_id"]
        reg_number = user["reg_number"]
        shortlisted_companies = user["shortlisted_companies"]

        # Log the values for checking
        logging.info(
            f"Checking user: chat_id={chat_id}, reg_number={reg_number}, shortlisted_companies={shortlisted_companies}")

        # Check if reg_number is in nxtresult
        logging.info(f"Checking if reg_number {reg_number} exists in nxtresult...")
        if reg_number in reg_numbers:
            logging.info(f"Match found for {reg_number}")

            # If shortlisted_companies already contains data, append the company_name
            if shortlisted_companies:
                updated_companies = shortlisted_companies + "," + company_name
            else:
                updated_companies = company_name

            # Update the shortlisted_companies for this user in the 'users' table
            logging.info(f"Updating shortlisted_companies for chat_id {chat_id}...")
            supabase.table("users").update({
                "shortlisted_companies": updated_companies
            }).eq("chat_id", chat_id).execute()

            # Send message to the user via the bot
            send_message_bot(chat_id, f"You're shortlisted for {company_name}")
        else:
            logging.info(f"No match found for {reg_number}")


def send_message_bot(chat_id, message):
    """
    Function to send a message to a Telegram bot.

    Args:
    chat_id (str): The chat ID of the user.
    message (str): The message to be sent to the user.
    """
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


# Sample usage
company_name = "Company A"
nxtresult = "RA211,RA3293892,RA2111030020008"  # Example registration numbers
fetch_and_update_users(company_name, nxtresult)
