FROM python:3.9-slim

WORKDIR /app

# Copy server, client, and requirements
COPY server.py .
COPY client.py .
COPY requirements.txt .

# Make scripts executable
RUN chmod +x server.py client.py

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8080

# Use environment variable for defaults
ENV USE_DEFAULTS=1

# Start server
CMD ["python3", "./server.py", "/app/content"]
