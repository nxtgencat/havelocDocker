import os

# Constants
WAIT_TIME = 10
RETRY_DELAY = 3
MAX_RETRIES = 3
DOWNLOAD_DIR = os.path.join(os.path.expanduser('~'), 'Downloads')

# URLs
SIGNIN_URL = "https://app.haveloc.com/"
NOTICE_URL = "https://app.haveloc.com/notice"

# XPath and CSS Selectors
SELECTORS = {
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

VALID_TEXTS = ["reg no", "registration number", "reg num", "registration no", "roll no", "roll number", "roll num"]