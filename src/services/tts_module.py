import wave
from google import genai
from google.genai import types
import os
from src.utils.time_logger import timeit
from dotenv import load_dotenv
import warnings
warnings.filterwarnings("ignore")

# Load environment variables from .env file
load_dotenv()

# Get GEMINI API key from environment variable
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

@timeit("Text-to-Speech")
def tts_generate(text, output_path, gemini_api_key):
    """
    Generate speech from text using Google Gemini API.
    
    Args:
        text (str): The text to convert to speech.
        output_path (str): Path to save the generated audio file.
        gemini_api_key (str): Google Gemini API key.
        
    Returns:
        str: Path to the saved audio file.
    """
    def save_wave(filename, pcm, channels=1, rate=24000, sample_width=2):
        with wave.open(filename, "wb") as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(sample_width)
            wf.setframerate(rate)
            wf.writeframes(pcm)
    
    # Initialize the Gemini client with the provided API key
    client = genai.Client(api_key=gemini_api_key)
    
    # Generate speech content using the Gemini model
    response = client.models.generate_content(
        model="gemini-2.5-flash-preview-tts",
        contents=f"Say cheerfully:{text}!",
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Kore")
                )
            ),
        )
    )

    # Extract audio data from the response and save it to the specified output path
    data = response.candidates[0].content.parts[0].inline_data.data
    
    # Save the audio data to a wave file
    save_wave(output_path, data)
    
    return output_path