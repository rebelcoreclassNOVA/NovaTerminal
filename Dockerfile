# Base image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy the zipped repo into the container
COPY Novaterminal.zip .

# Install unzip and Python dependencies if any
RUN apt-get update && apt-get install -y unzip && \
    unzip Novaterminal.zip -d ./ && \
    rm Novaterminal.zip

# Optional: install dependencies if you have a requirements.txt inside the zip
# RUN pip install -r requirements.txt

# Expose port for Cloud Run
ENV PORT=8080
EXPOSE 8080

# Run your main script (adjust path if your main.py is inside a folder after unzip)
CMD ["python", "Novaterminal/main.py"]
