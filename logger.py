import logging
import os
import sys
from datetime import datetime


def setup_logger(name='haveloc_scraper'):
    # Get the logger
    logger = logging.getLogger(name)

    # If the logger already has handlers, return it to avoid duplicate logging
    if logger.handlers:
        return logger

    # Create logs directory if it doesn't exist
    logs_dir = 'logs'
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)

    # Create log filename with timestamp
    log_filename = os.path.join(logs_dir, f'haveloc_scraper_{datetime.now().strftime("%Y%m%d")}.log')

    # Configure logger
    logger.setLevel(logging.INFO)

    # Prevent propagation to root logger
    logger.propagate = False

    # File handler
    file_handler = logging.FileHandler(log_filename)
    file_handler.setLevel(logging.INFO)

    # Console handler - specifically use stdout
    console_handler = logging.StreamHandler(sys.stdout)  # Changed this line
    console_handler.setLevel(logging.INFO)

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Add formatter to handlers
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger