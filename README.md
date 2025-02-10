# Haveloc Scraper

Haveloc Scraper is a Python-based web scraper designed to automate the extraction of email and notification data from Haveloc. This tool is useful for collecting information, processing attachments, and uploading relevant data to Supabase.

## Features

- **Headless Chrome Scraping**: Utilizes Selenium with ChromeDriver to navigate the Haveloc website.
- **Email Processing**: Logs into Haveloc, fetches emails, and extracts key information.
- **Attachment Handling**: Downloads and processes attachments for relevant data.
- **Data Extraction**: Extracts tabular data from emails and uploads it to Supabase.
- **Error Logging**: Captures and logs errors for troubleshooting.
- **Telegram Bot Integration**: Sends notifications via Telegram.

## Installation

### Prerequisites

- Python 3.x
- Google Chrome & ChromeDriver (ensure compatibility with your Chrome version)
- Docker (optional for containerized deployment)

### Setup

1. Clone the repository:
   ```sh
   git clone https://github.com/nxtgencat/HavelocScraper.git
   cd HavelocScraper
   ```
2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
3. Set up environment variables:
   Create a `.env` file and add the following variables:
   ```env
   SUPABASE_URL=<your_supabase_url>
   SUPABASE_API_KEY=<your_supabase_api_key>
   TELEGRAM_BOT_TOKEN=<your_telegram_bot_token>
   HAVELOC_CREDENTIALS=<your_haveloc_login_credentials>
   ```
4. Run the scraper:
   ```sh
   python main.py
   ```

## Docker Integration

To run the scraper in a Docker container:

1. Build the Docker image:
   ```sh
   docker build -t haveloc-scraper .
   ```
2. Run the container:
   ```sh
   docker run --env-file .env haveloc-scraper
   ```

## Supabase Database Schema

### Company Table
```sql
CREATE TABLE public.company (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    company_title TEXT NOT NULL,
    reg_number TEXT NOT NULL UNIQUE
) WITH (OIDS=FALSE);
```

### Users Table
```sql
CREATE TABLE public.users (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    chat_id TEXT NOT NULL UNIQUE,
    reg_number TEXT NOT NULL,
    shortlisted_companies TEXT
) WITH (OIDS=FALSE);
```

## Contributing
Feel free to fork this repository and submit pull requests. Any contributions are welcome!

## License
This project is licensed under the MIT License.