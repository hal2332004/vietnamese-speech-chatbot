from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import tempfile
import shutil
import os
import requests
import base64
import io
import logging
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

from transformers import pipeline
import asyncio
import os
import torch
import time
from functools import wraps
import warnings
import requests
from requests.exceptions import Timeout
import httpx
import json

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

@timeit("llama_cpp_chat_stream")
async def llama_cpp_chat_stream(prompt, server_url="http://localhost:8080/v1/chat/completions"):
    payload = {
        "model": "Vi-Qwen2-3B-RAG.Q8_0.gguf",
        "messages": [{"role": "user", "content": prompt}],
        "stream": True
    }
    async with httpx.AsyncClient(timeout=120) as client:
        async with client.stream("POST", server_url, json=payload) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line.removeprefix("data: ").strip()
                    if data and data != "[DONE]":
                        try:
                            obj = json.loads(data)
                            content = obj["choices"][0]["delta"].get("content", "")
                            if content:
                                yield content
                        except Exception:
                            continue

class SmartChabot:
    @timeit("SmartChabot.__init__")
    def __init__(self, qdrant_client, collection_name, embedding_model, llama_server_url="http://localhost:8080/v1/chat/completions"):
        self.qdrant_client = qdrant_client
        self.collection_name = collection_name
        
        # Move embedding model to CUDA if available
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.embedding_model = embedding_model.to(self.device)
        print(f"📢 Embedding model running on: {self.device}")
        
        self.llama_server_url = llama_server_url

    @timeit("SmartChabot.get_context_from_qdrant")
    def get_context_from_qdrant(self, question, k=3):
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

    # @timeit("SmartChabot.llama_cpp_answer_question")
    # async def llama_cpp_answer_question(self, question: str) -> str:
    #     try:
    #         context = self.get_context_from_qdrant(question)
    #         prompt = (
    #             "Hãy trả lời câu hỏi dựa trên ngữ cảnh dưới đây.\n\n"
    #             f"Ngữ cảnh:\n{context}\n\n"
    #             f"Câu hỏi:\n{question}\n\n"
    #         )
    #         # Gọi llama.cpp server
    #         answer = llama_cpp_chat(prompt, server_url=self.llama_server_url)
    #         return answer.strip()
    #     except Exception as e:
    #         return f"❌ Lỗi llama.cpp: {e}"
        
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Voice Chatbot API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def gemini_stt(audio_path: str, secret_key: str = None, model: str = "gemini-2.0-flash"):
    from google import genai
    client = genai.Client(api_key=secret_key)
    uploaded_file = client.files.upload(file=audio_path)

    response = client.models.generate_content(
        model=model,
        contents=[
            "Chuyển âm thanh sau thành văn bản tiếng Việt, chỉ trả lại phần nội dung lời nói. Không thêm tiêu đề, mô tả hay giải thích nào khác.",
            uploaded_file
        ]
    )

    token_info = client.models.count_tokens(
        model=model,
        contents=[uploaded_file]
    )

    return response.text, token_info

TTS_URL = "http://localhost:5000/tts"

load_dotenv()
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_HOST = os.getenv("QDRANT_HOST")
embedding_model = SentenceTransformer('Alibaba-NLP/gte-multilingual-base', trust_remote_code=True)
qdrant_client = QdrantClient(
    api_key=QDRANT_API_KEY, 
    url=QDRANT_HOST, 
    https=True,
)
collection_name = "syllabus_embeddings_gte"
chatbot = SmartChabot(qdrant_client, collection_name, embedding_model)

@app.get("/")
async def root():
    return {"message": "Voice Chatbot API is running"}

@app.get("/health")
async def health_check():
    """Check if all dependent services are running"""
    services = {
        "tts": TTS_URL
    }
    
    status = {}
    for service, url in services.items():
        try:
            response = requests.get(url.replace("/stt", "/").replace("/tts", "/"), timeout=15)
            status[service] = "healthy" if response.status_code == 200 else "unhealthy"
        except:
            status[service] = "unavailable"
    
    return {"status": status}

@app.post("/chat-voice")
async def chat_voice(
    file: UploadFile = File(...), 
    model: str = Form("gemini-2.0-flash")
):
    """
    Complete voice chatbot pipeline:
    Audio Input → STT → RAG → TTS → Audio Output
    """
    
    if not file.content_type or not file.content_type.startswith('audio/'):
        raise HTTPException(status_code=400, detail="File must be an audio file")
    
    # Create temporary file for audio processing
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        logger.info("Starting voice chat pipeline")
        
        # Step 1: Speech to Text (GỌI TRỰC TIẾP HÀM gemini_stt)
        logger.info("Step 1: Converting speech to text")
        secret_key = os.getenv("GEMINI_API_KEY")
        if not secret_key:
            raise HTTPException(status_code=500, detail="GEMINI_API_KEY not set")
        try:
            text, token_info = gemini_stt(tmp_path, secret_key, model)
            text = text.strip()
        except Exception as e:
            logger.error(f"STT failed: {str(e)}")
            raise HTTPException(status_code=500, detail="Speech-to-text conversion failed")
        
        if not text:
            raise HTTPException(status_code=400, detail="No speech detected in audio")
            
        logger.info(f"STT result: {text}")

        # Step 2: RAG Processing (replace HTTP call with direct call)
        logger.info("Step 2: Processing question with RAG")
        try:
            answer = await chatbot.llama_cpp_answer_question(text)
            answer = answer.replace("**", "")
        except Exception as e:
            logger.error(f"RAG failed: {str(e)}")
            raise HTTPException(status_code=500, detail="Question processing failed")
        if not answer:
            answer = "Xin lỗi, tôi không thể trả lời câu hỏi này."
        logger.info(f"RAG answer: {answer}")

        # Step 3: Text to Speech
        logger.info("Step 3: Converting answer to speech")
        tts_response = requests.post(
            TTS_URL, 
            json={"text": answer, "language": "vi"},
            timeout=60
        )
        
        if tts_response.status_code != 200:
            logger.error(f"TTS failed: {tts_response.status_code} - {tts_response.text}")
            raise HTTPException(status_code=500, detail="Text-to-speech conversion failed")

        tts_result = tts_response.json()
        audio_base64 = tts_result.get("audio_base64", "")
        
        if not audio_base64:
            raise HTTPException(status_code=500, detail="TTS returned no audio data")

        # Decode and return audio
        try:
            audio_bytes = base64.b64decode(audio_base64)
            audio_stream = io.BytesIO(audio_bytes)
            
            logger.info("Voice chat pipeline completed successfully")
            
            return StreamingResponse(
                audio_stream, 
                media_type="audio/wav",
                headers={
                    "X-Transcription": text,
                    "X-Answer": answer,
                    "Content-Disposition": "inline; filename=response.wav"
                }
            )
            
        except Exception as e:
            logger.error(f"Audio decoding failed: {str(e)}")
            raise HTTPException(status_code=500, detail="Audio processing failed")

    except requests.exceptions.Timeout:
        raise HTTPException(status_code=408, detail="Request timeout - service took too long to respond")
    except requests.exceptions.ConnectionError:
        raise HTTPException(status_code=503, detail="Cannot connect to required services")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    finally:
        # Clean up temporary file
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

@app.post("/chat-text-stream")
async def chat_text_stream(request: dict):
    """
    Text-only chat endpoint with streaming response
    """
    question = request.get("question", "").strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question is required")

    context = chatbot.get_context_from_qdrant(question)
    # prompt = (
    #     "Hãy trả lời câu hỏi dựa trên ngữ cảnh dưới đây, nếu ngữ cảnh.\n\n"
    #     "Nếu ngữ cảnh không liên quan đến câu hỏi, bạn có thể trả lời dựa trên kiến thức của mình, mà không cần thông báo rằng ngữ cảnh không phù hợp.\n\n"
    #     f"Ngữ cảnh:\n{context}\n\n"
    #     f"Câu hỏi:\n{question}\n\n"
    # )

    prompt = (
        "Bạn là một trợ lý AI thân thiện và súc tích. Hãy trả lời CÂU HỎI bên dưới.\n"
        "Nếu NGỮ CẢNH chứa thông tin phù hợp, hãy sử dụng nó.\n"
        "Nếu không, hãy trả lời ngay dựa trên kiến thức của bạn — KHÔNG cần nói về ngữ cảnh.\n"
        "Không cần nói 'dựa trên ngữ cảnh' hay 'ngữ cảnh không liên quan'. Trả lời trực tiếp.\n\n"
        f"NGỮ CẢNH:\n{context}\n\n"
        f"CÂU HỎI:\n{question}\n\n"
        "TRẢ LỜI:"
    )

    # Không await ở đây, chỉ return generator
    return StreamingResponse(llama_cpp_chat_stream(prompt), media_type="text/plain")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)