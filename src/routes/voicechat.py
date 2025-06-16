from fastapi import APIRouter, UploadFile
import os
from src.services.stt_module import transcribe_audio
from src.services.ttt_module import generate_answer
from src.services.tts_module import tts_generate
from dotenv import load_dotenv
import warnings
warnings.filterwarnings("ignore")

# Load environment variables from .env file
load_dotenv()

# Get GEMINI API key from environment variable
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Create a FastAPI router for voice chat
router = APIRouter()

@router.post("/voicechat")
async def voice_chat(file: UploadFile):
    """
    Handle voice chat requests by transcribing audio, generating an answer, and converting it to speech.
    
    Args:
        file (UploadFile): The uploaded audio file.
        
    Returns:
        dict: A dictionary
    """

    input_path = f"temp/{file.filename}"
    with open(input_path, "wb") as f:
        f.write(await file.read())

    question = transcribe_audio(input_path)
    answer = generate_answer(question)
    output_path = f"temp/tts_{file.filename}"
    tts_generate(answer, output_path, GEMINI_API_KEY)

    return {"question": question, "answer": answer, "audio_url": f"/temp/tts_{file.filename}"}
    