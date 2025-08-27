# Use Python 3.12 slim base image
FROM python:3.12-slim

# Set working directory inside the container
WORKDIR /app

# Copy your application code into the container
COPY . .

# Expose the port your app will listen on
ENV PORT=8080
EXPOSE 8080

# Command to run your app (adjust if your entrypoint is different)
CMD ["python", "main.py"]
