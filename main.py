import logging
import os
import time

# Configure the logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler("haveloc_scraper.log"),
        logging.StreamHandler()
    ]
)

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as conditions
from selenium.webdriver.support.ui import WebDriverWait

from data_utils import get_haveloc_credentials
from my_workbook import file_data_extract
from supabase_api import fetch_and_update_users, upload_company


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')  # Clear screen based on OS


logging.info('Setting up environment')

chrome_options = Options()
chrome_options.add_argument('--headless')  # Run in headless mode
chrome_options.add_argument('--disable-gpu')  # Disable GPU acceleration
chrome_options.add_argument('--no-sandbox')  # Required for running in Docker
chrome_options.add_argument('--disable-dev-shm-usage')  # Fix for low memory environments
chrome_options.add_argument('--remote-debugging-port=9222')  # Fix for the DevToolsActivePort issue

service = Service('/usr/local/bin/chromedriver')  # Specify the location of ChromeDriver

driver = webdriver.Chrome(service=service, options=chrome_options)

# URLs and Selectors
signin_url = "https://app.haveloc.com/"
notice_url = "https://app.haveloc.com/notice"
selectors = {
    "email_list_container": "//*[@id='root']/div[3]/div[2]/div/div[1]/div[3]",
    "email_element": "./div",
    "load_more_button": "load_more_btn",
    "email_subject": ".//div[@class='email-subject']/span",
    "email_subject_detail": "//*[@id='root']/div[3]/div[2]/div/div[2]/div[1]/div[1]/div[1]",
    "email_date_detail": "//*[@id='root']/div[3]/div[2]/div/div[2]/div[1]/div[2]/div[1]/div[2]/div[2]",
    "table_container": "//*[@id='root']/div[3]/div[2]/div/div[2]/div[1]/div[2]/div[2]/div/div[2]/div/table",
    "table_header": "//*[@id='root']/div[3]/div[2]/div/div[2]/div[1]/div[2]/div[2]/div/div[2]/div/table/tbody/tr[1]",
    "all_rows": "//*[@id='root']/div[3]/div[2]/div/div[2]/div[1]/div[2]/div[2]/div/div[2]/div/table/tbody/tr",
    "attachment_notification": "//*[@id='root']/div[3]/div[2]/div/div[2]/div[1]/div[2]/div[2]/div/div[1]",
    "attachment_download_button": "//*[@id='root']/div[3]/div[2]/div/div[2]/div[1]/div[2]/div[2]/div/div[1]/div/div/div[2]/span",
    "cancel_button": "/html/body/div[3]/div[3]/div/div[3]/button[1]/span[1]",
    "login_page_identify": "//*[@id='root']/div[2]/div[1]/div[1]"
}

valid_texts = ["reg no", "registration number", "reg num", "registration no", "roll no", "roll number", "roll num"]


def inject_credentials():
    """Inject cookies and local storage from saved credentials."""
    saved_data = get_haveloc_credentials()
    for cookie in saved_data.get("cookies", []):
        driver.add_cookie(cookie)
    for key, value in saved_data.get("localStorage", {}).items():
        driver.execute_script(f"window.localStorage.setItem('{key}', '{value}');")


def login_haveloc():
    """Log into Haveloc app, retrying if login fails."""
    driver.get(signin_url)
    inject_credentials()
    driver.refresh()
    while True:
        try:
            login_element = WebDriverWait(driver, 5).until(
                conditions.presence_of_element_located((By.XPATH, selectors["login_page_identify"]))
            )
            if login_element.text.lower() == "log in to haveloc":
                logging.warning("Cannot login to Haveloc app. Retrying...")
                driver.refresh()
                inject_credentials()
                time.sleep(3)
        except Exception:
            logging.info("Logged in successfully. Now reading notifications.")
            driver.get(notice_url)
            time.sleep(5)
            break


login_haveloc()


def check_each_email(email_element, index):
    """Process individual email for details and attachments."""
    try:
        email_subject_span = email_element.find_elements(By.XPATH, selectors["email_subject"])
        if email_subject_span:
            process_email_details(email_element, index, "new", True)
        else:
            process_email_details(email_element, index, "seen", False)

    except Exception as e:
        logging.error(f"Error processing email {index}: {e}")


def process_email_details(email_element, index, status, extract):
    """Process email details and attachments or table for both new and seen emails.

    Args:
    - email_element: The email element to process.
    - index: The index of the email.
    - status: The status of the email, either 'new' or 'seen'.
    - extract: Boolean flag to indicate if table checking should be done.
    """
    try:
        logging.info(f"Email {index}: {status.capitalize()}")
        email_element.click()
        time.sleep(2)

        subject_element = driver.find_element(By.XPATH, selectors["email_subject_detail"])
        email_date_element = driver.find_element(By.XPATH, selectors["email_date_detail"])
        company_name = subject_element.text
        logging.info(f"  Subject: {subject_element.text}")
        logging.info(f"  Date: {email_date_element.text}")

        # If 'extract' is True, check for the table first
        if extract:
            table_data = check_table_header()  # Check for table and extract data
            if table_data != "Table container not found." and table_data != "No valid column found in table_header.":
                logging.info(f"  Data found. Extracted data: {table_data}")
                # Proceed with any further actions for the table
                fetch_and_update_users(company_name, table_data)
                upload_response = upload_company(company_name, table_data)
                logging.info("Data uploaded to Supabase.")

            else:
                logging.warning("No table data found. Checking for attachment...")

                # Check for attachments if no table is found
                attachment_element = driver.find_element(By.XPATH, selectors["attachment_notification"])
                if attachment_element.text.strip() == "":
                    logging.info("  No attachment for this email.")
                else:
                    logging.info("  Attachment found for this email.")
                    attachment_download_button = driver.find_element(By.XPATH, selectors["attachment_download_button"])
                    attachment_download_button.click()
                    time.sleep(5)

                    download_dir = os.path.expanduser('~') + "/Downloads"
                    downloaded_file = max([os.path.join(download_dir, f) for f in os.listdir(download_dir)],
                                          key=os.path.getctime)
                    logging.info(f"Extracting data: {downloaded_file}")
                    file_extracted_result = file_data_extract(downloaded_file)


                    fetch_and_update_users(company_name, file_extracted_result)
                    upload_response = upload_company(company_name, file_extracted_result)
                    logging.info("Data uploaded to Supabase.")

        else:
            # If 'extract' is False, do nothing (skip everything)
            logging.info(f"  Skipping extraction and attachment checks for email {index}.")

    except Exception as e:
        logging.error(f"Error processing email {index}: {e}")


def extract_table_column_data(column_index):
    """
    Extracts the data from a specific column (excluding the header row)
    and returns it as a comma-separated string.
    """
    all_rows = driver.find_elements(By.XPATH, selectors["all_rows"])
    column_data = []

    # Start the loop from the second row to skip the first one
    for row in all_rows[1:]:
        td_in_row = row.find_elements(By.TAG_NAME, "td")
        # Extract text from the specified column index and strip whitespace
        cell_text = td_in_row[column_index - 1].text.strip()
        column_data.append(cell_text)

    # Strip any extra whitespace from all elements in the list before joining
    cleaned_column_data = [data.strip() for data in column_data]

    return ", ".join(cleaned_column_data)


def check_table_header():
    # Check if the table container exists
    try:
        table_container = driver.find_element(By.XPATH, selectors["table_container"])
        logging.info("Table container found.")  # Log confirmation when table container is found
    except:
        logging.error("Table container not found.")
        return "Table container not found."
    try:
        table_header = driver.find_element(By.XPATH, selectors["table_header"])

        # Check all td elements within table_header
        td_elements = table_header.find_elements(By.TAG_NAME, "td")
        for index, td in enumerate(td_elements, start=1):  # Start indexing from 1 for readability
            # Get the text content of the td, convert to lowercase, and check for matches
            td_text = td.text.strip().lower()
            if td_text in [text.lower() for text in valid_texts]:
                logging.info(f"Found valid text: '{td_text}' in column {index}")

                # Extract all data from the found column
                column_data = extract_table_column_data(index)

                # Return the extracted data as a comma-separated string
                return column_data

        else:
            logging.warning("No valid column found in table_header.")
            return "No valid column found in table_header."

    except:
        logging.error("Table header not found.")
        return "Table header not found."


def run_haveloc_scrape():
    """Continuously process emails, refreshing if 'Load More' button is encountered."""
    try:
        cancel_button = WebDriverWait(driver, 10).until(
            conditions.element_to_be_clickable((By.XPATH, selectors["cancel_button"]))
        )
        cancel_button.click()
        logging.info("Install App Popup Closed Successfully.")
    except Exception as e:
        logging.error("Error Closing the Install App Popup: %s", e)

    try:
        while True:
            email_list_container = WebDriverWait(driver, 10).until(
                conditions.presence_of_element_located((By.XPATH, selectors["email_list_container"]))
            )
            email_elements = email_list_container.find_elements(By.XPATH, selectors["email_element"])

            if email_elements:
                for index, email_element in enumerate(email_elements, start=1):
                    if selectors["load_more_button"] in email_element.get_attribute('class'):
                        logging.info("Reached 'Load More' button. Refreshing page to start over.")
                        driver.refresh()
                        time.sleep(3)
                        return
                    clear_screen()
                    check_each_email(email_element, index)
                    time.sleep(5)
            else:
                logging.info("No emails found in the email list.")
                break
    except Exception as e:
        logging.error("Error: %s", e)



# Main loop to continuously process emails
while True:
    run_haveloc_scrape()