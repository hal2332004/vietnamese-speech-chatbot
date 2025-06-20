from fastapi import APIRouter, UploadFile
import os
from src.services.stt_module import transcribe_audio
from src.services.ttt_module import generate_answer
from src.services.tts_module import tts_generate
import warnings
warnings.filterwarnings("ignore")

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
    tts_generate(answer, output_path)

    return {"question": question, "answer": answer, "audio_url": f"/temp/tts_{file.filename}"}
    