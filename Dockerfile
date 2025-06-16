# Use the official Python 3.11 slim image as the base image
FROM python:3.11-slim

# Set the working directory inside the container to /app
WORKDIR /app

# Copy the requirements.txt file into the container at /app
COPY requirements.txt .

# Install Python dependencies from requirements.txt without using cache
RUN pip install --no-cache-dir -r requirements.txt

# Copy all files from the current directory to /app in the container
COPY . .

# Set the default command to run the FastAPI app with Uvicorn on port 5500
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "5500"]
