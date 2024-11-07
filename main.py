import json
import os
import time
from flask import Flask, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from api import upload_company
from data_reader import reg_extract

# Initialize Flask app
app = Flask(__name__)

chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--remote-debugging-port=9222')

service = Service('/usr/local/bin/chromedriver')

driver = webdriver.Chrome(service=service, options=chrome_options)

signin_url = "https://app.haveloc.com/"
driver.get(signin_url)

# Load saved data from JSON
with open("saved_data.json", "r") as json_file:
    saved_data = json.load(json_file)

cookies = saved_data.get("cookies", [])
for cookie in cookies:
    driver.add_cookie(cookie)

local_storage = saved_data.get("localStorage", {})
for key, value in local_storage.items():
    driver.execute_script(f"window.localStorage.setItem('{key}', '{value}');")

driver.refresh()

notice_url = "https://app.haveloc.com/notice"
driver.get(notice_url)
time.sleep(5)

email_list_container_selector = "//*[@id='root']/div[3]/div[2]/div/div[1]/div[3]"
email_element_selector = "./div"
load_more_button_selector = "load_more_btn"
email_subject_selector = ".//div[@class='email-subject']/span"
email_subject_detail_selector = "//*[@id='root']/div[3]/div[2]/div/div[2]/div[1]/div[1]/div[1]"
email_date_detail_selector = "//*[@id='root']/div[3]/div[2]/div/div[2]/div[1]/div[2]/div[1]/div[2]/div[2]"
attachment_notification_selector = "//*[@id='root']/div[3]/div[2]/div/div[2]/div[1]/div[2]/div[2]/div/div[1]"
attachment_download_button_selector = "//*[@id='root']/div[3]/div[2]/div/div[2]/div[1]/div[2]/div[2]/div/div[1]/div/div/div[2]/span"
cancel_button_selector = "/html/body/div[3]/div[3]/div/div[3]/button[1]/span[1]"

@app.route('/start-scraping', methods=['GET'])
def start_scraping():
    try:
        readLatestMails()
        return jsonify({"status": "success", "message": "Scraping started successfully!"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

def readLatestMails():
    # Locate and click the button to read the latest emails
    # Locate and click the Cancel button
    while True:
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


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # Use the PORT environment variable
    app.run(host='0.0.0.0', port=port)
