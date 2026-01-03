FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/server.py .

# Copy credentials (you'll mount these as volumes)
# COPY credentials.json .
# COPY token.pickle .

# Make the script executable
RUN chmod +x server.py

# Run the MCP server
CMD ["python", "server.py"]