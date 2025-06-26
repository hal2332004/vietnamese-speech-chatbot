from transformers import pipeline
from src.utils.time_logger import timeit
import warnings
warnings.filterwarnings("ignore")

@timeit("Speech-to-Text")
def transcribe_audio(filename):
    """
    Transcribe audio file to text using HuggingFace pipeline.
    
    Args:
        filename (str): Path to the audio file.
        
    Returns:
        str: Transcribed text.
    """
    pipe = pipeline("automatic-speech-recognition", model="vinai/PhoWhisper-base")
    result = pipe(filename)
    return result['text']