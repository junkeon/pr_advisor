# Use the official Python image from the Docker Hub
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install vim
RUN apt-get update && apt-get install -y vim

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY main.py .
COPY response_schema.py .
COPY .env .

# Command to run the application
CMD ["python", "main.py"]