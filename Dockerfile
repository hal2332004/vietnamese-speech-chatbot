# Dockerfile
FROM python:3.11-slim

# Tạo thư mục làm việc
WORKDIR /workspace

# Cài PortAudio 
RUN apt-get update && apt-get install -y portaudio19-dev

# # Cài đặt git-lfs (để clone repo lớn từ Hugging Face nếu cần)
# RUN apt-get update && apt-get install -y git-lfs
# RUN git-lfs install
# RUN apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy toàn bộ mã nguồn vào container
COPY . .

# Cài đặt dependencies
RUN pip install --no-cache-dir -r /workspace/requirements.txt

# # Tải model về
# RUN python -c "import os; from transformers import AutoTokenizer, AutoModelForCausalLM; \
#                AutoTokenizer.from_pretrained('google/gemma-7b', token='${HUGGINGFACE_TOKEN}'); \
#                 AutoModelForCausalLM.from_pretrained('google/gemma-7b', token='${HUGGINGFACE_TOKEN}')"


# Mở port nếu cần
EXPOSE 8000

# Lệnh mặc định để chạy
CMD ["python", "src/demo/full_demo.py"]
