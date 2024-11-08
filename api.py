from supabase import create_client, Client

# Replace these with your Supabase URL and API Key
SUPABASE_URL = "https://zlygxmxwzigeuecbwukw.supabase.co"
SUPABASE_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpseWd4bXh3emlnZXVlY2J3dWt3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzA5MDY5MTAsImV4cCI6MjA0NjQ4MjkxMH0.ikIH_7vobQdWDz945ID17LLdRX8D5JCfut0_Z2P47sU"

# Create the Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_API_KEY)


def upload_company(company_title: str, reg_number: str):
    """
    Function to upload company_name and reg_no into the 'company' table in Supabase.

    Args:
    company_name (str): The name of the company.
    reg_no (str): The registration number of the company.

    Returns:
    response: The response from the Supabase insert operation.
    """
    # Insert data into the company table
    response = supabase.table("company").insert({
        "company_title": company_title,
        "reg_number": reg_number
    }).execute()

    # Return the response from Supabase
    return response

