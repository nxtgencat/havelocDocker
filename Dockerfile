# Use a slim Python base image
FROM python:3.13-slim

# Set timezone
ENV TZ="Asia/Kolkata"

# Set working directory
WORKDIR /app

# Install chromium browser in a single layer
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . /app

# Create necessary directories
RUN mkdir -p /root/Downloads /app/logs

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    CHROMIUM_PATH=/usr/bin/chromium \
    CHROMEDRIVER_PATH=/usr/bin/chromedriver

# Command to run the application
ENTRYPOINT ["python", "main.py"]