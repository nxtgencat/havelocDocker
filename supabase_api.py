import logging
import os

import dotenv
from supabase import create_client
from telegram_bot import send_message_bot

dotenv.load_dotenv()
# Replace these with your Supabase URL and API Key
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_API_KEY = os.environ.get("SUPABASE_API_KEY")

# Create the Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_API_KEY)


def upload_company(company_title: str, reg_number: str):
    # Insert data into the company table
    response = supabase.table("company").insert({
        "company_title": company_title,
        "reg_number": reg_number
    }).execute()

    # Return the response from Supabase
    return response


def fetch_and_update_users(company_name: str, nxtresult: str):
    # Split nxtresult into a list of registration numbers and strip whitespace from each
    reg_numbers = [reg.strip() for reg in nxtresult.split(',')]

    # Fetch all users from the 'users' table
    logging.info("Fetching users from the database...")
    users = supabase.table("users").select("*").execute()

    logging.info(f"Fetched {len(users.data)} users from the database.")

    for user in users.data:
        chat_id = user["chat_id"]
        reg_number = user["reg_number"].strip()  # Strip whitespace from database reg_number
        shortlisted_companies = user["shortlisted_companies"]

        # Log the values for checking
        logging.info(
            f"Checking user: chat_id={chat_id}, reg_number={reg_number}, shortlisted_companies={shortlisted_companies}")

        # Check if reg_number is in nxtresult
        logging.info(f"Checking if reg_number {reg_number} exists in sheet...")
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
            send_message_bot(chat_id, f"You're listed for {company_name}")
        else:
            logging.info(f"No match found for {reg_number}")

