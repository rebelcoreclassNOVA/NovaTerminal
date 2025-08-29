# Use an official Python runtime as the base image
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Copy requirements first (for caching)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project
COPY . /app

# Expose the port your app runs on
EXPOSE 8000

# Start the web server (adjust "main:app" to match your entrypoint)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
