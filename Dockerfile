# Use the official Python 3.11 slim image as the base image
FROM python:3.11-slim

# Set the working directory inside the container to /app
WORKDIR /app

# Install ffmpeg
RUN apt-get update && apt-get install -y ffmpeg && apt-get clean

# Copy the requirements.txt file into the container at /app
COPY requirements.txt .

# Install Python dependencies from requirements.txt without using cache
RUN pip install --no-cache-dir -r requirements.txt

# Copy all files from the current directory to /app in the container
COPY . .

EXPOSE 8000
# Set the default command to run the FastAPI app with Uvicorn on port 8000
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
