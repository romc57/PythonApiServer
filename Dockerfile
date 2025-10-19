# Use Python 3.12 slim image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies including Chrome
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    gnupg \
    unzip \
    xvfb \
    x11vnc \
    fluxbox \
    wmctrl \
    && wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome-keyring.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome-keyring.gpg] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Copy consolidated requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy API type directories
COPY apis/ ./apis/

# Copy the main API server files
COPY base_api.py .
COPY api_server.py .

# Create auth directory
RUN mkdir -p /app/auth

# Expose port
EXPOSE 8081

# Set environment variables
ENV PYTHONPATH=/app
ENV FLASK_ENV=production

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8081/health || exit 1

# Run the API server
CMD ["python", "api_server.py"]
