# Dockerfile
FROM python:3.11-slim

# Tạo thư mục làm việc
WORKDIR /workspace

# Cài ffmpeg
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy toàn bộ mã nguồn vào container
COPY . .

# Cài đặt dependencies
RUN pip install --no-cache-dir -r /workspace/requirements.txt 

# Mở port nếu cần
EXPOSE 8000

# Lệnh mặc định để chạy
CMD ["python", "src/demo/full_demo.py"]
