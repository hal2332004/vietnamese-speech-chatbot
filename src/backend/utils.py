# import sounddevice as sd
from scipy.io.wavfile import write
from transformers import pipeline
import asyncio
import os
import librosa
import torch
import time
from functools import wraps
import warnings
import requests
from requests.exceptions import Timeout


warnings.filterwarnings("ignore")

def timeit(module_name=""):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            result = func(*args, **kwargs)
            end = time.time()
            duration = end - start
            print(f"⏱️ [{module_name}] hoàn thành trong {duration:.2f} giây.")
            return result
        return wrapper
    return decorator

def llama_cpp_chat(prompt, server_url="http://localhost:8080/v1/chat/completions"):
    """
    Gọi llama.cpp server (OpenAI API style endpoint /v1/chat/completions).
    """
    payload = {
        "model": "llama",  # adjust if your server expects a model name
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    try:
        resp = requests.post(server_url, json=payload, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        # OpenAI-style: answer is in choices[0]['message']['content']
        return data["choices"][0]["message"]["content"]
    except Timeout:
        return "❌ Lỗi llama.cpp: Server không phản hồi (timeout). Vui lòng kiểm tra lại server hoặc thử lại sau."
    except Exception as e:
        return f"❌ Lỗi llama.cpp: {e}"

class SmartChabot:
    def __init__(self, qdrant_client, collection_name, embedding_model, llama_server_url="http://localhost:8080/v1/chat/completions"):
        self.qdrant_client = qdrant_client
        self.collection_name = collection_name
        
        # Move embedding model to CUDA if available
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.embedding_model = embedding_model.to(self.device)
        print(f"📢 Embedding model running on: {self.device}")
        
        # self.gemini_model = gemini_model
        # self.model = model
        # self.tokenizer = tokenizer
        self.llama_server_url = llama_server_url

    def get_context_from_qdrant(self, question, k=2):
        # Ensure input is on the same device as the model
        with torch.amp.autocast(device_type='cuda'):
            embedding = self.embedding_model.encode(
                f"Tài liệu để truy xuất: {question}",
                convert_to_tensor=True,
                device=self.device
            ).cpu().numpy().tolist()  # Convert back to CPU for Qdrant
            
        response = self.qdrant_client.search( 
            collection_name=self.collection_name,
            query_vector=embedding, 
            limit=k,
            with_payload=True
        )
        context = "\n".join([point.payload.get("text", "") for point in response])

        # test
        for i, point in enumerate(response, 1):
            context_text = point.payload.get("text", "")
            print(f"\n--- Context #{i} ---\n{context_text}")

        return context

    async def llama_cpp_answer_question(self, question: str) -> str:
        try:
            context = self.get_context_from_qdrant(question)
            prompt = (
                "Chú ý các yêu cầu sau:\n"
                "- Câu trả lời phải chính xác và đầy đủ nếu ngữ cảnh có câu trả lời.\n"
                "- Chỉ sử dụng các thông tin có trong ngữ cảnh được cung cấp.\n"
                "- Chỉ cần từ chối trả lời và không suy luận gì thêm nếu ngữ cảnh không có câu trả lời.\n\n"
                "Hãy trả lời câu hỏi dựa trên ngữ cảnh dưới đây.\n\n"
                f"### Ngữ cảnh:\n{context}\n\n"
                f"### Câu hỏi:\n{question}\n\n"
                "### Trả lời:"
            )
            # Gọi llama.cpp server
            answer = llama_cpp_chat(prompt, server_url=self.llama_server_url)
            return answer.strip()
        except Exception as e:
            return f"❌ Lỗi llama.cpp: {e}"