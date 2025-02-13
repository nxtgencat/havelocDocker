import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as conditions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import (
    TimeoutException,
    StaleElementReferenceException,
    ElementClickInterceptedException, WebDriverException
)

from config import *
from data_utils import get_haveloc_credentials
from my_workbook import file_data_extract
from supabase_api import fetch_and_update_users, upload_company

# Initialize logger
import logging
logger = logging.getLogger('haveloc_scraper')


class HavelocScraper:
    def __init__(self):
        self.driver = None
        self.setup_driver()

    def setup_driver(self):
        """Initialize and configure Chromium WebDriver."""
        logger.info("Setting up Chromium WebDriver")
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.binary_location = "/usr/bin/chromium"  # Specify Chromium binary location

            logger.debug("Chromium options configured: %s", chrome_options.arguments)

            # Use system's chromedriver
            service = Service("/usr/bin/chromedriver")
            self.driver = webdriver.Chrome(service=service, options=chrome_options)

            logger.info("Chromium WebDriver successfully initialized")

            # Log browser details
            browser_version = self.driver.capabilities.get('browserVersion', 'unknown')
            chromium_version = self.driver.capabilities.get('chrome', {}).get('chromedriverVersion', 'unknown')
            logger.info(f"Browser version: {browser_version}")
            logger.info(f"ChromeDriver version: {chromium_version}")

        except WebDriverException as e:
            logger.error(f"Failed to initialize WebDriver: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during WebDriver initialization: {str(e)}")
            raise

    def inject_credentials(self):
        """Inject cookies and local storage from saved credentials."""
        logger.info("Starting credentials injection")
        saved_data = get_haveloc_credentials()
        logger.debug(
            f"Retrieved credentials with {len(saved_data.get('cookies', []))} cookies and {len(saved_data.get('localStorage', {}))} localStorage items")

        try:
            # Clear existing cookies and storage
            self.driver.delete_all_cookies()
            self.driver.execute_script("window.localStorage.clear();")
            logger.debug("Cleared existing cookies and localStorage")

            # Add cookies
            for cookie in saved_data.get("cookies", []):
                clean_cookie = {
                    key: cookie[key]
                    for key in ['name', 'value', 'domain', 'path', 'secure', 'httpOnly']
                    if key in cookie
                }
                try:
                    self.driver.add_cookie(clean_cookie)
                    logger.debug(f"Successfully set cookie: {clean_cookie['name']}")
                except Exception as e:
                    logger.warning(f"Failed to set cookie {clean_cookie['name']}: {str(e)}")

            # Add localStorage items
            for key, value in saved_data.get("localStorage", {}).items():
                try:
                    safe_value = value.replace("'", "\\'")
                    self.driver.execute_script(f"window.localStorage.setItem('{key}', '{safe_value}');")
                    logger.debug(f"Successfully set localStorage item: {key}")
                except Exception as e:
                    logger.warning(f"Failed to set localStorage item {key}: {str(e)}")

            logger.info("Credentials injection completed successfully")
        except Exception as e:
            logger.error(f"Error during credentials injection: {str(e)}")
            raise

    def safe_click(self, element, wait_time=2):
        """Safely click an element with retry logic."""
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                element.click()
                time.sleep(wait_time)
                return True
            except (StaleElementReferenceException, ElementClickInterceptedException) as e:
                if attempt == max_attempts - 1:
                    logger.error(f"Failed to click element after {max_attempts} attempts: {str(e)}")
                    return False
                time.sleep(1)
        return False

    def wait_for_element(self, by, selector, timeout=WAIT_TIME):
        """Wait for element with error handling."""
        try:
            return WebDriverWait(self.driver, timeout).until(
                conditions.presence_of_element_located((by, selector))
            )
        except TimeoutException:
            return None

    def extract_table_column_data(self, column_index):
        """Extract data from a specific table column."""
        try:
            all_rows = self.driver.find_elements(By.XPATH, SELECTORS["all_rows"])
            column_data = []

            for row in all_rows[1:]:
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) >= column_index:
                    cell_text = cells[column_index - 1].text.strip()
                    if cell_text:
                        column_data.append(cell_text)

            return ", ".join(column_data) if column_data else None

        except Exception as e:
            logger.error(f"Error extracting column data: {str(e)}")
            return None

    def handle_popup(self):
        """Handle install app popup."""
        try:
            cancel_button = self.wait_for_element(By.XPATH, SELECTORS["cancel_button"], timeout=5)
            if cancel_button and self.safe_click(cancel_button):
                logger.info("Install App Popup Closed Successfully")
        except Exception as e:
            logger.debug(f"No popup found or already closed: {str(e)}")

    def login_haveloc(self):
        """Enhanced login function with better error handling."""
        retry_count = 0

        while retry_count < MAX_RETRIES:
            try:
                self.driver.get(SIGNIN_URL)
                self.inject_credentials()
                self.driver.refresh()
                time.sleep(2)

                self.driver.get(NOTICE_URL)
                email_container = self.wait_for_element(By.XPATH, SELECTORS["email_list_container"])

                if email_container:
                    logger.info("Login successful")
                    return True

            except Exception as e:
                retry_count += 1
                logger.error(f"Login attempt {retry_count} failed: {str(e)}")
                if retry_count >= MAX_RETRIES:
                    return False
                time.sleep(RETRY_DELAY)

        return False

    def check_table_data(self):
        """Check table data with improved error handling."""
        try:
            table_container = self.wait_for_element(By.XPATH, SELECTORS["table_container"])
            if not table_container:
                logger.error("Table container not found.")
                return None

            logger.info("Table container found.")
            table_header = self.wait_for_element(By.XPATH, SELECTORS["table_header"])
            if not table_header:
                return None

            td_elements = table_header.find_elements(By.TAG_NAME, "td")
            for index, td in enumerate(td_elements, start=1):
                td_text = td.text.strip().lower()
                if td_text in [text.lower() for text in VALID_TEXTS]:
                    logger.info(f"Found valid text: '{td_text}' in column {index}")
                    return self.extract_table_column_data(index)

            logger.warning("No valid column found in table_header.")
            return None

        except Exception as e:
            logger.error(f"Error checking table data: {str(e)}")
            return None

    def process_attachment(self, company_name):
        """Process email attachment with improved error handling."""
        try:
            download_button = self.wait_for_element(By.XPATH, SELECTORS["attachment_download_button"])
            if download_button and self.safe_click(download_button):
                time.sleep(5)  # Wait for download

                # Get the latest downloaded file
                downloaded_file = max(
                    [os.path.join(DOWNLOAD_DIR, f) for f in os.listdir(DOWNLOAD_DIR)],
                    key=os.path.getctime
                )

                logger.info(f"Processing attachment: {downloaded_file}")

                # Verify file exists and is readable
                if not os.path.exists(downloaded_file):
                    logger.error(f"Downloaded file not found: {downloaded_file}")
                    return False

                extracted_data = file_data_extract(downloaded_file)
                if extracted_data:
                    return self.process_data(company_name, extracted_data)
                else:
                    logger.error("Failed to extract data from attachment")
                    return False

        except Exception as e:
            logger.error(f"Error processing attachment: {str(e)}")
        return False

    def process_data(self, company_name, data):
        """Process extracted data with improved error handling."""
        try:
            # Add error handling for network connectivity
            if not self._check_network_connectivity():
                logger.error("Network connectivity issues detected")
                return False

            fetch_and_update_users(company_name, data)
            upload_company(company_name, data)
            logger.info("Data uploaded to Supabase successfully")
            return True
        except Exception as e:
            logger.error(f"Error processing data: {str(e)}")
            return False

    def _check_network_connectivity(self):
        """Check network connectivity before making API calls."""
        import socket
        try:
            # Try to connect to Supabase (or any reliable host)
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return True
        except OSError:
            return False

    def process_email(self, email_element, index):
        """Process individual email with improved error handling."""
        try:
            email_subject_span = email_element.find_elements(By.XPATH, SELECTORS["email_subject"])
            is_new = bool(email_subject_span)
            status = "New" if is_new else "Seen"
            logger.info(f"Email {index}: {status}")

            if not is_new:
                logger.info(f"  Skipping email {index} as it's already seen")
                return

            if not self.safe_click(email_element):
                return

            time.sleep(2)

            subject = self.wait_for_element(By.XPATH, SELECTORS["email_subject_detail"])
            date_element = self.wait_for_element(By.XPATH, SELECTORS["email_date_detail"])

            if subject and date_element:
                company_name = subject.text
                logger.info(f"  Subject: {company_name}")
                logger.info(f"  Date: {date_element.text}")

                table_data = self.check_table_data()
                if table_data:
                    return self.process_data(company_name, table_data)

                logger.warning("No table data found. Checking for attachment...")

                attachment_element = self.wait_for_element(By.XPATH, SELECTORS["attachment_notification"])
                if attachment_element and attachment_element.text.strip():
                    logger.info("  Attachment found for this email.")
                    return self.process_attachment(company_name)
                else:
                    logger.info("  No attachment for this email.")

        except Exception as e:
            logger.error(f"Error processing email {index}: {str(e)}")

    def run_haveloc_scrape(self):
        """Main scraping function with improved error handling."""
        self.handle_popup()

        try:
            while True:
                email_container = self.wait_for_element(By.XPATH, SELECTORS["email_list_container"])
                if not email_container:
                    logger.info("No emails found in the email list.")
                    time.sleep(RETRY_DELAY)
                    continue

                email_elements = email_container.find_elements(By.XPATH, SELECTORS["email_element"])
                if not email_elements:
                    logger.info("No emails found")
                    time.sleep(RETRY_DELAY)
                    self.driver.refresh()
                    self.handle_popup()  # Handle popup after refresh
                    continue

                for index, email_element in enumerate(email_elements, start=1):
                    if SELECTORS["load_more_button"] in email_element.get_attribute('class'):
                        logger.info("Reached load more button, refreshing page")
                        self.driver.refresh()
                        self.handle_popup()  # Handle popup after refresh
                        time.sleep(RETRY_DELAY)
                        break

                    self.process_email(email_element, index)
                    time.sleep(5)  # Wait between emails

        except Exception as e:
            logger.error(f"Error in main scraping loop: {str(e)}")

    def cleanup(self):
        """Clean up resources."""
        try:
            if self.driver:
                self.driver.quit()
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")

    def run(self):
        """Main run method with error handling and cleanup."""
        logger.info("Starting Haveloc scraper")

        try:
            if self.login_haveloc():
                while True:
                    try:
                        self.run_haveloc_scrape()
                        time.sleep(RETRY_DELAY)
                    except Exception as e:
                        logger.error(f"Error in scraping loop: {str(e)}")
                        time.sleep(RETRY_DELAY * 2)  # Wait longer after an error
                        self.driver.refresh()  # Try refreshing the page
            else:
                logger.error("Failed to login")
        except KeyboardInterrupt:
            logger.info("Scraper stopped by user")
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
        finally:
            self.cleanup()