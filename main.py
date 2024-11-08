import os
import time

import logging
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
from my_workbook import reg_extract
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
    "attachment_notification": "//*[@id='root']/div[3]/div[2]/div/div[2]/div[1]/div[2]/div[2]/div/div[1]",
    "attachment_download_button": "//*[@id='root']/div[3]/div[2]/div/div[2]/div[1]/div[2]/div[2]/div/div[1]/div/div/div[2]/span",
    "cancel_button": "/html/body/div[3]/div[3]/div/div[3]/button[1]/span[1]",
    "login_page_identify": "//*[@id='root']/div[2]/div[1]/div[1]"
}

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

def process_email(email_element, index):
    """Process individual email for details and attachments."""
    try:
        email_subject_span = email_element.find_elements(By.XPATH, selectors["email_subject"])
        if email_subject_span:
            logging.info(f"Email {index}: New")
            email_element.click()
            time.sleep(2)

            subject_element = driver.find_element(By.XPATH, selectors["email_subject_detail"])
            email_date_element = driver.find_element(By.XPATH, selectors["email_date_detail"])

            logging.info(f"  Subject: {subject_element.text}")
            logging.info(f"  Date: {email_date_element.text}")

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
                nxtresult = reg_extract(downloaded_file)

                company_name = subject_element.text
                fetch_and_update_users(company_name, nxtresult)
                upload_response = upload_company(company_name, nxtresult)
                logging.info("Data uploaded to Supabase: %s", upload_response)
        else:
            logging.info(f"Email {index}: Seen")
            email_element.click()
            time.sleep(2)

            subject_element = driver.find_element(By.XPATH, selectors["email_subject_detail"])
            email_date_element = driver.find_element(By.XPATH, selectors["email_date_detail"])

            logging.info(f"  Subject: {subject_element.text}")
            logging.info(f"  Date: {email_date_element.text}")

            attachment_element = driver.find_element(By.XPATH, selectors["attachment_notification"])
            if attachment_element.text.strip() == "":
                logging.info("  No attachment for this email.")
            else:
                logging.info("  Attachment found for this email.")
    except Exception as e:
        logging.error(f"Error processing email {index}: {e}")

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

                    process_email(email_element, index)
                    time.sleep(1)
            else:
                logging.info("No emails found in the email list.")
                break
    except Exception as e:
        logging.error("Error: %s", e)

    clear_screen()

# Main loop to continuously process emails
while True:
    run_haveloc_scrape()
