# Use official Python runtime
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set the PORT environment variable
ENV PORT 8080

# Expose the port
EXPOSE 8080

# Run the app
CMD ["python", "app.py"]
