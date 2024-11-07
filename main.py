import json
import os
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from api import upload_company
from data_reader import reg_extract

chrome_options = Options()
chrome_options.add_argument('--headless')  # Run in headless mode
chrome_options.add_argument('--disable-gpu')  # Disable GPU acceleration
chrome_options.add_argument('--no-sandbox')  # Required for running in Docker
chrome_options.add_argument('--disable-dev-shm-usage')  # Fix for low memory environments
chrome_options.add_argument('--remote-debugging-port=9222')  # Fix for the DevToolsActivePort issue

service = Service('/usr/local/bin/chromedriver')  # Specify the location of ChromeDriver

driver = webdriver.Chrome(service=service, options=chrome_options)

# Login URL (or any URL you want to test)
signin_url = "https://app.haveloc.com/"

# Open the signin URL
driver.get(signin_url)

# Load the saved data from the JSON file
with open("saved_data.json", "r") as json_file:
    saved_data = json.load(json_file)

# Inject cookies and local storage
cookies = saved_data.get("cookies", [])
for cookie in cookies:
    driver.add_cookie(cookie)

local_storage = saved_data.get("localStorage", {})
for key, value in local_storage.items():
    driver.execute_script(f"window.localStorage.setItem('{key}', '{value}');")

# Refresh the page to apply cookies and local storage
driver.refresh()

# Navigate to the notice page
notice_url = "https://app.haveloc.com/notice"
driver.get(notice_url)

# Add a delay to allow dynamic content to load
time.sleep(5)

# Element Selectors (Updated to XPath)

# Email List Container
email_list_container_selector = "//*[@id='root']/div[3]/div[2]/div/div[1]/div[3]"
# Individual Email Elements
email_element_selector = "./div"  # To locate each email item within the email list container
# "Load More" Button
load_more_button_selector = "load_more_btn"  # Class name to identify the "Load More" button
# Email Subject
email_subject_selector = ".//div[@class='email-subject']/span"  # Inside each email element
# Email Subject and Date on Detail Page
email_subject_detail_selector = "//*[@id='root']/div[3]/div[2]/div/div[2]/div[1]/div[1]/div[1]"
email_date_detail_selector = "//*[@id='root']/div[3]/div[2]/div/div[2]/div[1]/div[2]/div[1]/div[2]/div[2]"
# Attachment Notification Element
attachment_notification_selector = "//*[@id='root']/div[3]/div[2]/div/div[2]/div[1]/div[2]/div[2]/div/div[1]"
# Attachment Download Button
attachment_download_button_selector = "//*[@id='root']/div[3]/div[2]/div/div[2]/div[1]/div[2]/div[2]/div/div[1]/div/div/div[2]/span"
# Cancel Button
cancel_button_selector = "/html/body/div[3]/div[3]/div/div[3]/button[1]/span[1]"


def readLatestMails(host=os.getenv('HOST', '0.0.0.0'), port=int(os.getenv('PORT', 5000))):
    # Locate and click the button to read the latest emails
    # Locate and click the Cancel button
    try:
        cancel_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, cancel_button_selector))
        )
        cancel_button.click()
        print("Cancel button clicked successfully.")
    except Exception as e:
        print("Error clicking the Cancel button:", e)

    # Proceed with email processing after the button click
    try:
        while True:  # Loop to check emails
            # Locate the email list container
            email_list_container = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, email_list_container_selector))
            )

            # Get all children of the email list container
            email_elements = email_list_container.find_elements(By.XPATH, email_element_selector)

            if email_elements:
                for index, email_element in enumerate(email_elements, start=1):
                    try:
                        # Check if it's the "Load More" button
                        if load_more_button_selector in email_element.get_attribute('class'):
                            print("Reached 'Load More' button. Refreshing page to start over.")
                            # Refresh the page and restart the email checking process
                            driver.refresh()
                            time.sleep(3)  # Wait for the page to reload and stabilize
                            return  # Exit the function and start over

                        # Locate the email subject span
                        email_subject_span = email_element.find_elements(By.XPATH, email_subject_selector)

                        # Proceed regardless of whether the span exists or not
                        if email_subject_span:
                            print(f"\nEmail {index}:")
                            print(f"  Subject: New")
                            # Click on the email to open it
                            email_element.click()

                            # Wait for the email detail page to load
                            time.sleep(2)  # You can adjust the delay as needed

                            try:
                                # Locate the subject and email date elements
                                subject_element = driver.find_element(By.XPATH, email_subject_detail_selector)
                                email_date_element = driver.find_element(By.XPATH, email_date_detail_selector)

                                # Print the subject, email date, and index
                                print(f"  Subject: {subject_element.text}")
                                print(f"  Date: {email_date_element.text}")

                                # Locate the attachment notification element
                                attachment_element = driver.find_element(By.XPATH, attachment_notification_selector)

                                # Check if the attachment element is empty or not
                                if attachment_element.text.strip() == "":
                                    print("  No attachment for this email.")
                                else:
                                    print("  Attachment found for this email.")
                                    # Click to download the attachment
                                    attachment_download_button = driver.find_element(By.XPATH,
                                                                                     attachment_download_button_selector)
                                    attachment_download_button.click()

                                    # Wait for the file to download (you may need to adjust this time)
                                    time.sleep(5)

                                    # Click to download the attachment
                                    attachment_download_button = driver.find_element(By.XPATH,
                                                                                     attachment_download_button_selector)
                                    attachment_download_button.click()

                                    # Wait for the file to download (you may need to adjust this time)
                                    time.sleep(5)

                                    # Assuming the downloaded file is in the default download directory
                                    download_dir = os.path.expanduser('~') + "/Downloads"  # Adjust this if needed
                                    downloaded_files = os.listdir(download_dir)

                                    # Get the latest downloaded file (assuming the newest one is the attachment)
                                    downloaded_file = max([os.path.join(download_dir, f) for f in downloaded_files],
                                                          key=os.path.getctime)

                                    # Invoke reg_extract with the downloaded file path
                                    print(f"Extracting data: {downloaded_file}")
                                    nxtresult = reg_extract(downloaded_file)
                                    upload_response = upload_company(company_name, nxtresult)
                                    print("Data uploaded to Supabase:", upload_response)

                            except Exception as e:
                                print("Error checking attachment:", e)
                        else:
                            print(f"\nEmail {index}: Seen")
                            # Click on the email to open it
                            email_element.click()

                            # Wait for the email detail page to load
                            time.sleep(2)  # You can adjust the delay as needed

                            try:
                                # Locate the subject and email date elements
                                subject_element = driver.find_element(By.XPATH, email_subject_detail_selector)
                                email_date_element = driver.find_element(By.XPATH, email_date_detail_selector)

                                company_name = subject_element.text

                                # Print the subject, email date, and index
                                print(f"  Subject: {subject_element.text}")
                                print(f"  Date: {email_date_element.text}")

                                # Locate the attachment notification element
                                attachment_element = driver.find_element(By.XPATH, attachment_notification_selector)

                                # Check if the attachment element is empty or not
                                if attachment_element.text.strip() == "":
                                    print("  No attachment for this email.")
                                else:
                                    print("  Attachment found for this email.")


                            except Exception as e:
                                print("Error checking attachment:", e)

                        # Add a short delay before moving to the next email
                        time.sleep(1)

                    except Exception as e:
                        print(f"Error processing email {index}: {e}")

            else:
                print("No emails found in the email list.")
                break  # Exit if no emails are found

    except Exception as e:
        print("Error:", e)


# Continuously process emails and refresh if 'Load More' is encountered
while True:
    readLatestMails()
