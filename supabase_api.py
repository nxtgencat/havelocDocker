import logging

from supabase import create_client, Client
from telegram_bot import send_message_bot

# Replace these with your Supabase URL and API Key
SUPABASE_URL = "https://zlygxmxwzigeuecbwukw.supabase.co"
SUPABASE_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpseWd4bXh3emlnZXVlY2J3dWt3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzA5MDY5MTAsImV4cCI6MjA0NjQ4MjkxMH0.ikIH_7vobQdWDz945ID17LLdRX8D5JCfut0_Z2P47sU"

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
