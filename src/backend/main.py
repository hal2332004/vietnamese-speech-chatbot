from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import tempfile
import shutil
import os
import base64
import io
import logging
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from transformers import pipeline
import asyncio
import torch
from requests.exceptions import Timeout
import httpx
import json
from utils import timeit
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# --- TTS imports from tts_api.py ---
import torchaudio
from tqdm import tqdm
from underthesea import sent_tokenize
from vinorm import TTSnorm
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import Xtts

load_dotenv()
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_HOST = os.getenv("QDRANT_HOST")
embedding_model = SentenceTransformer('Alibaba-NLP/gte-multilingual-base', trust_remote_code=True)
qdrant_client = QdrantClient(
    api_key=QDRANT_API_KEY, 
    url=QDRANT_HOST, 
    https=True,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- TTS model initialization (from tts_api.py) ---
XTTS_MODEL = None
gpt_cond_latent = None
speaker_embedding = None

device = "cuda:0" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device}")

xtts_checkpoint = "model/model.pth"
xtts_config = "model/config.json"
xtts_vocab = "model/vocab.json"
speaker_audio_file = "model/samples/nu-luu-loat.wav"

def preprocess_text(text, language="vi"):
    if language == "vi":
        text = TTSnorm(text, unknown=False, lower=False, rule=True)
    if language in ["ja", "zh-cn"]:
        sentences = text.split("。")
    else:
        sentences = sent_tokenize(text)
    chunks = []
    chunk_i = ""
    len_chunk_i = 0
    for sentence in sentences:
        chunk_i += " " + sentence
        len_chunk_i += len(sentence.split())
        if len_chunk_i > 30:
            chunks.append(chunk_i.strip())
            chunk_i = ""
            len_chunk_i = 0
    if (len(chunks) > 0) and (len_chunk_i < 15):
        chunks[-1] += chunk_i
    else:
        chunks.append(chunk_i)
    return chunks

def tts(
    model: Xtts,
    text: str,
    language: str,
    gpt_cond_latent: torch.Tensor,
    speaker_embedding: torch.Tensor,
    verbose: bool = False,
):
    chunks = preprocess_text(text, language)
    wav_chunks = []
    for text_chunk in tqdm(chunks, disable=not verbose):
        if text_chunk.strip() == "":
            continue
        wav_chunk = model.inference(
            text=text_chunk,
            language=language,
            gpt_cond_latent=gpt_cond_latent,
            speaker_embedding=speaker_embedding,
            length_penalty=1.0,
            repetition_penalty=10.0,
            top_k=10,
            top_p=0.5,
        )
        wav_chunk["wav"] = torch.tensor(wav_chunk["wav"])
        wav_chunks.append(wav_chunk["wav"])
    out_wav = torch.cat(wav_chunks, dim=0).unsqueeze(0).cpu()
    return out_wav

app = FastAPI(title="Voice Chatbot API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    global XTTS_MODEL, gpt_cond_latent, speaker_embedding
    print("Loading TTS model...")
    config = XttsConfig()
    config.load_json(xtts_config)
    XTTS_MODEL = Xtts.init_from_config(config)
    XTTS_MODEL.load_checkpoint(config,
                              checkpoint_path=xtts_checkpoint,
                              vocab_path=xtts_vocab,
                              use_deepspeed=False)
    XTTS_MODEL.to(device)
    gpt_cond_latent, speaker_embedding = XTTS_MODEL.get_conditioning_latents(
        audio_path=speaker_audio_file,
        gpt_cond_len=XTTS_MODEL.config.gpt_cond_len,
        max_ref_length=XTTS_MODEL.config.max_ref_len,
        sound_norm_refs=XTTS_MODEL.config.sound_norm_refs,
    )
    print("TTS model loaded successfully!")

class SmartChabot:
    @timeit("SmartChabot.__init__")
    def __init__(self, qdrant_client, collection_name, embedding_model, llama_server_url="http://localhost:8080/v1/chat/completions"):
        self.qdrant_client = qdrant_client
        self.collection_name = collection_name
        
        # Move embedding model to CUDA if available
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.embedding_model = embedding_model.to(self.device)
        print(f"📢 Embedding model running on: {self.device}")
        
        self.llama_server_url = llama_server_url.strip()  # Đảm bảo không có ký tự lạ

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

    @timeit("llama_cpp_chat_stream")
    async def llama_cpp_chat_stream(self, prompt):
        server_url = self.llama_server_url  # Đã được strip ở __init__
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

    def is_in_domain(self, question, threshold=0.55, k=3):
        """
        Trả về True nếu câu hỏi thuộc in-domain (cosine similarity với knowledge base >= threshold)
        """
        # Lấy embedding của câu hỏi
        with torch.amp.autocast(device_type='cuda'):
            question_emb = self.embedding_model.encode(
                f"Tài liệu để truy xuất: {question}",
                convert_to_tensor=True,
                device=self.device
            ).cpu().numpy().reshape(1, -1)
        # Lấy top-k context từ Qdrant
        response = self.qdrant_client.search(
            collection_name=self.collection_name,
            query_vector=question_emb.flatten().tolist(),
            limit=k,
            with_vectors=True,
            with_payload=True
        )
        # Lấy embedding của các context
        kb_embs = []
        for point in response:
            if hasattr(point, "vector"):
                kb_embs.append(point.vector)
            elif "vector" in point.__dict__:
                kb_embs.append(point.__dict__["vector"])
        if not kb_embs:
            return False
        kb_embs = np.array(kb_embs)
        # Tính cosine similarity
        sims = cosine_similarity(question_emb, kb_embs)[0]
        max_sim = np.max(sims)
        logger.info(f"Max similarity for question '{question}': {max_sim:.4f}")
        return max_sim >= threshold


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

    return response.text, None

collection_name = "syllabus_embeddings_gte"
chatbot = SmartChabot(qdrant_client, collection_name, embedding_model)

@app.get("/")
async def root():
    return {"message": "Voice Chatbot API is running"}

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
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        logger.info("Starting voice chat pipeline")
        # Step 1: Speech to Text
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

        # Step 2: RAG Processing (same as chat-text-stream)
        logger.info("Step 2: Processing question with RAG")
        context = chatbot.get_context_from_qdrant(text)
        in_domain = chatbot.is_in_domain(text)
        logger.info(f"in_domain: {in_domain}")

        if in_domain:
            prompt_indomain = (
                "Hãy trả lời câu hỏi dựa trên ngữ cảnh dưới đây.\n\n"
                f"Ngữ cảnh:\n{context}\n\n"
                f"Câu hỏi:\n{text}\n\n"
            )
            prompt = prompt_indomain
        else:
            prompt_outdomain = (
                "Hãy trả lời câu hỏi sau.\n\n"
                f"Câu hỏi:\n{text}\n\n"
            )
            prompt = prompt_outdomain

        # Step 3: Get answer from LLM (llama_cpp_chat_stream)
        logger.info("Step 3: Getting answer from LLM")
        answer_chunks = []
        async for chunk in chatbot.llama_cpp_chat_stream(prompt):
            answer_chunks.append(chunk)
        answer = "".join(answer_chunks).strip()
        logger.info(f"LLM answer: {answer}")

        # Step 4: Text to Speech (direct call, not HTTP)
        logger.info("Step 4: Converting answer to speech")
        try:
            audio_tensor = tts(
                model=XTTS_MODEL,
                text=answer,
                language="vi",
                gpt_cond_latent=gpt_cond_latent,
                speaker_embedding=speaker_embedding,
                verbose=False
            )
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
                torchaudio.save(tmp_file.name, audio_tensor, 24000)
                with open(tmp_file.name, 'rb') as f:
                    audio_data = f.read()
                os.unlink(tmp_file.name)
            audio_stream = io.BytesIO(audio_data)
            audio_stream.seek(0)
            logger.info("Voice chat pipeline completed successfully")
            # --- Encode headers as base64 to avoid non-ASCII issues ---
            x_transcription_b64 = base64.b64encode(text.encode("utf-8")).decode("ascii")
            x_answer_b64 = base64.b64encode(answer.encode("utf-8")).decode("ascii")
            return StreamingResponse(
                audio_stream, 
                media_type="audio/wav",
                headers={
                    "X-Transcription": x_transcription_b64,
                    "X-Answer": x_answer_b64,
                    "Content-Disposition": "inline; filename=response.wav"
                }
            )
        except Exception as e:
            logger.error(f"Audio decoding failed: {str(e)}")
            raise HTTPException(status_code=500, detail="Audio processing failed")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    finally:
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
    in_domain = chatbot.is_in_domain(question)
    print(f"in_domain: {in_domain}...")  
    # Đảm bảo không truyền URL có ký tự lạ (nếu có custom server_url thì .strip())
    if in_domain:
        prompt_indomain = (
            "Hãy trả lời câu hỏi dựa trên ngữ cảnh dưới đây.\n\n"
            f"Ngữ cảnh:\n{context}\n\n"
            f"Câu hỏi:\n{question}\n\n"
        )
        return StreamingResponse(
            chatbot.llama_cpp_chat_stream(prompt_indomain), 
            media_type="text/plain"
        )
    else:
        prompt_outdomain = (
            "Hãy trả lời câu hỏi sau.\n\n"
            f"Câu hỏi:\n{question}\n\n"
        )
        return StreamingResponse(
            chatbot.llama_cpp_chat_stream(prompt_outdomain), 
            media_type="text/plain"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)