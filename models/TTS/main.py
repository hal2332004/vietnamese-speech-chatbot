from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import torch
import torchaudio
from tqdm import tqdm
from underthesea import sent_tokenize
from vinorm import TTSnorm
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import Xtts
import tempfile
import os
import io
import base64
from typing import Optional
import uvicorn

app = FastAPI(
    title="Vietnamese TTS API",
    description="Text-to-Speech API using XTTS model for Vietnamese",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class TTSRequest(BaseModel):
    text: str
    language: str = "vi"

class TTSResponse(BaseModel):
    success: bool
    audio_base64: Optional[str] = None
    format: str = "wav"
    sample_rate: int = 24000
    error: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    model_loaded: bool

# Global variables for model
XTTS_MODEL = None
gpt_cond_latent = None
speaker_embedding = None

# Initialize TTS model
device = "cuda:0" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device}")

xtts_checkpoint = "model/model.pth"
xtts_config = "model/config.json"
xtts_vocab = "model/vocab.json"
speaker_audio_file = "model/samples/nu-luu-loat.wav"

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

    # Get speaker conditioning
    gpt_cond_latent, speaker_embedding = XTTS_MODEL.get_conditioning_latents(
        audio_path=speaker_audio_file,
        gpt_cond_len=XTTS_MODEL.config.gpt_cond_len,
        max_ref_length=XTTS_MODEL.config.max_ref_len,
        sound_norm_refs=XTTS_MODEL.config.sound_norm_refs,
    )

    print("TTS model loaded successfully!")

def preprocess_text(text, language="vi"):
    if language == "vi":
        text = TTSnorm(text, unknown=False, lower=False, rule=True)
    
    # split text into sentences
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
    # preprocess text
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

@app.post("/tts", response_model=TTSResponse)
async def text_to_speech(request: TTSRequest):
    try:
        if not request.text:
            raise HTTPException(status_code=400, detail="Text is required")
        
        print(f"Processing TTS for text: {request.text[:50]}...")
        
        # Generate audio
        audio_tensor = tts(
            model=XTTS_MODEL,
            text=request.text,
            language=request.language,
            gpt_cond_latent=gpt_cond_latent,
            speaker_embedding=speaker_embedding,
            verbose=False
        )
        
        # Convert tensor to wav file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
            torchaudio.save(tmp_file.name, audio_tensor, 24000)
            
            # Read the file and convert to base64
            with open(tmp_file.name, 'rb') as f:
                audio_data = f.read()
                audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            
            # Clean up temp file
            os.unlink(tmp_file.name)
        
        return TTSResponse(
            success=True,
            audio_base64=audio_base64,
            format="wav",
            sample_rate=24000
        )
        
    except Exception as e:
        print(f"Error in TTS: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tts/file")
async def text_to_speech_file(request: TTSRequest):
    try:
        if not request.text:
            raise HTTPException(status_code=400, detail="Text is required")
        
        print(f"Processing TTS for text: {request.text[:50]}...")
        
        # Generate audio
        audio_tensor = tts(
            model=XTTS_MODEL,
            text=request.text,
            language=request.language,
            gpt_cond_latent=gpt_cond_latent,
            speaker_embedding=speaker_embedding,
            verbose=False
        )
        
        # Create temporary file
        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
        torchaudio.save(tmp_file.name, audio_tensor, 24000)
        tmp_file.close()
        
        return FileResponse(
            tmp_file.name,
            media_type='audio/wav',
            filename='output.wav'
        )
        
    except Exception as e:
        print(f"Error in TTS: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy",
        model_loaded=XTTS_MODEL is not None
    )

@app.get("/")
async def root():
    return {
        "message": "Vietnamese TTS API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == '__main__':
    uvicorn.run(
        "main:app",  # Change this to your filename if different
        host="0.0.0.0",
        port=5000,
        reload=True,
        log_level="info"
    )