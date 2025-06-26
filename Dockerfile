# Dockerfile for a FastAPI application with NVIDIA CUDA support and ffmpeg installed
# Base image with NVIDIA CUDA runtime for Ubuntu 22.04
FROM nvidia/cuda:12.4.1-runtime-ubuntu22.04

# Set the working directory inside the container to /app
WORKDIR /app

# Install Python + pip 
RUN apt-get update && \
    apt-get install -y python3.11 python3.11-venv python3-pip ffmpeg \
                       build-essential cmake libasound2-dev libsndfile1 && \
    rm -rf /var/lib/apt/lists/*

# Symlink python3.11 -> python
RUN ln -sf /usr/bin/python3.11 /usr/bin/python && \
    ln -sf /usr/bin/pip3 /usr/bin/pip

# Copy the requirements.txt file into the container at /app
COPY requirements.txt .

# Install Python dependencies from requirements.txt without using cache
RUN pip install --no-cache-dir -r requirements.txt

# Copy all files from the current directory to /app in the container
COPY . .

EXPOSE 8000
# Set the default command to run the FastAPI app with Uvicorn on port 8000
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
