# Use a slim Python base image
FROM python:3.13-slim

# Set timezone
ENV TZ="Asia/Kolkata"

# Set working directory
WORKDIR /app

# Install chromium browser in a single layer
RUN apt-get update && apt-get install -y \
    chromium \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . /app

# Command to run the application
ENTRYPOINT ["python", "main.py"]