# Use a slim Python base image
FROM python:3.13-slim

# Set timezone
ENV TZ="Asia/Kolkata"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . /app

# Ensure ChromeDriver is in PATH
ENV PATH="/usr/bin:${PATH}"

# Command to run the application
ENTRYPOINT ["python", "main.py"]