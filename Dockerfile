# Use an official Python base image
FROM python:3.13.3-slim

# Install Node.js and npm
RUN apt-get update && apt-get install -y nodejs npm

# Set the working directory in the container
WORKDIR /app

ENV SERVER_DOMAIN=http://4.247.151.9

# Copy requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project into the container
COPY . .

# Expose the application port
EXPOSE 5001

# Set the entrypoint command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5001"]