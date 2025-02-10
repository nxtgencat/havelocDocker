import sys
import os
from scraper import HavelocScraper
from logger import setup_logger


def main():
    # Setup logger
    logger = setup_logger()

    try:
        # Create logs and downloads directories if they don't exist
        for directory in ['logs', os.path.expanduser('~/Downloads')]:
            if not os.path.exists(directory):
                os.makedirs(directory)
                logger.info(f"Created directory: {directory}")

        # Initialize and run scraper
        scraper = HavelocScraper()
        scraper.run()

    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()