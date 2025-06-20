import os
from src.utils.time_logger import timeit
from tts.api import TTS 
import warnings
warnings.filterwarnings("ignore")


@timeit("Text-to-Speech")
def tts_generate(text, output_path):
    """
    Generate speech from text using Google Gemini API.
    
    Args:
        text (str): The text to convert to speech.
        output_path (str): Path to save the generated audio file.
        
    Returns:
        str: Path to the saved audio file.
    """

    tts = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2")
    tts.tts_to_file(text=text, file_path=output_path)
    return output_path