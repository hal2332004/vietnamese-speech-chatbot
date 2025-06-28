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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Voice Chatbot API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API endpoints for the three services
STT_URL = "http://localhost:12345/stt"
RAG_URL = "http://localhost:12346/ask"
TTS_URL = "http://localhost:12347/tts"

@app.get("/")
async def root():
    return {"message": "Voice Chatbot API is running"}

@app.get("/health")
async def health_check():
    """Check if all dependent services are running"""
    services = {
        "stt": STT_URL,
        "rag": RAG_URL,
        "tts": TTS_URL
    }
    
    status = {}
    for service, url in services.items():
        try:
            response = requests.get(url.replace("/stt", "/").replace("/ask", "/").replace("/tts", "/"), timeout=5)
            status[service] = "healthy" if response.status_code == 200 else "unhealthy"
        except:
            status[service] = "unavailable"
    
    return {"status": status}

@app.post("/chat-voice")
async def chat_voice(
    file: UploadFile = File(...), 
    model: str = Form("gemini-2.5-flash-lite-preview-06-17")
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
        
        # Step 1: Speech to Text
        logger.info("Step 1: Converting speech to text")
        with open(tmp_path, "rb") as audio_file:
            stt_response = requests.post(
                STT_URL,
                files={"file": ("recording.wav", audio_file, "audio/wav")},
                data={"model": model},
                timeout=30
            )
        
        if stt_response.status_code != 200:
            logger.error(f"STT failed: {stt_response.status_code} - {stt_response.text}")
            raise HTTPException(status_code=500, detail="Speech-to-text conversion failed")

        stt_result = stt_response.json()
        text = stt_result.get("text", "").strip()
        
        if not text:
            raise HTTPException(status_code=400, detail="No speech detected in audio")
            
        logger.info(f"STT result: {text}")

        # Step 2: RAG Processing
        logger.info("Step 2: Processing question with RAG")
        rag_response = requests.post(
            RAG_URL, 
            json={"question": text},
            timeout=30
        )
        
        if rag_response.status_code != 200:
            logger.error(f"RAG failed: {rag_response.status_code} - {rag_response.text}")
            raise HTTPException(status_code=500, detail="Question processing failed")

        rag_result = rag_response.json()
        answer = rag_result.get("answer", "").strip()
        
        if not answer:
            answer = "Xin lỗi, tôi không thể trả lời câu hỏi này."
            
        logger.info(f"RAG answer: {answer}")

        # Step 3: Text to Speech
        logger.info("Step 3: Converting answer to speech")
        tts_response = requests.post(
            TTS_URL, 
            json={"text": answer, "language": "vi"},
            timeout=30
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

@app.post("/chat-text")
async def chat_text(request: dict):
    """
    Text-only chat endpoint for testing
    """
    question = request.get("question", "").strip()
    
    if not question:
        raise HTTPException(status_code=400, detail="Question is required")
    
    try:
        # RAG Processing
        rag_response = requests.post(
            RAG_URL, 
            json={"question": question},
            timeout=30
        )
        
        if rag_response.status_code != 200:
            raise HTTPException(status_code=500, detail="Question processing failed")

        rag_result = rag_response.json()
        answer = rag_result.get("answer", "").strip()
        
        return {"question": question, "answer": answer}
        
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=408, detail="Request timeout")
    except requests.exceptions.ConnectionError:
        raise HTTPException(status_code=503, detail="Cannot connect to RAG service")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)