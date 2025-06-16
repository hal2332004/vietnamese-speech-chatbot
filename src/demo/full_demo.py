import os
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
from qdrant_client import QdrantClient
from dotenv import load_dotenv
import asyncio
from sentence_transformers import SentenceTransformer
import wave
from google import genai
from google.genai import types
import time
import functools
import warnings

warnings.filterwarnings("ignore")

# Load environment variables from .env file
load_dotenv()

# Get GEMINI API key from environment variable
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Get QDRANT API key and host from environment variables
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_HOST = os.getenv("QDRANT_HOST")

# Get HUGGINGFACE Token from environment variable
# hf_token = os.getenv("HUGGINGFACE_TOKEN")

# Create pipeline for text generation using HuggingFace token
tokenizer = AutoTokenizer.from_pretrained("tiiuae/falcon-rw-1b") #token=hf_token)
model = AutoModelForCausalLM.from_pretrained("tiiuae/falcon-rw-1b") #token=hf_token)
text_gen_pipeline = pipeline("text-generation", model=model, tokenizer=tokenizer, device=0)


# Initialize Qdrant client for Docker 
qdrant_client = QdrantClient(
    api_key=QDRANT_API_KEY,  # Qdrant API key
    url=QDRANT_HOST,  # Qdrant server URL 
    https=True,  # Use HTTPS
)

# Collection name for Qdrant
collection_name = "syllabus_embeddings"

# Initialize SentenceTransformer model
embedding_model = SentenceTransformer("intfloat/multilingual-e5-large-instruct")

# Ensure ffmpeg is in the PATH for audio processing
# os.environ["PATH"] += os.pathsep + "C:\\ProgramData\\chocolatey\\lib\\ffmpeg\\tools\\ffmpeg\\bin"

# Timeit decorator to measure execution time of functions (async)
def timeit_async(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = await func(*args, **kwargs)
        end_time = time.perf_counter()
        print(f"Thời gian xử lý {func.__name__}: {end_time - start_time:.2f} giây")
        return result
    return wrapper

# Timeit decorator to measure execution time of functions (sync)
def timeit_sync(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        print(f"Thời gian xử lý {func.__name__}: {end_time - start_time:.2f} giây")
        return result
    return wrapper

# PhoWhisper transcription
@timeit_sync
def transcribe_audio_pho(filename):
    pipe = pipeline("automatic-speech-recognition", model="vinai/PhoWhisper-base")
    result = pipe(filename)
    return result['text']

# Define the SmartChabot class
class SmartChabot:
    def __init__(self, qdrant_client, collection_name, model, gemini_model="models/gemini-2.0-flash-exp"):
        self.qdrant_client = qdrant_client
        self.collection_name = collection_name
        self.model = model
        self.gemini_model = gemini_model

    def get_context_from_qdrant(self, question, k=29):
        """Retrieve context from Qdrant based on the question."""
        embedding = self.model.encode(f"Tài liệu để truy xuất: {question}").tolist()
        response = self.qdrant_client.search(
            collection_name=self.collection_name,
            query_vector=embedding,
            limit=k,
            with_payload=True
        )

        context = "\n".join([point.payload.get("văn bản", "") for point in response])
        return context
    
    def generate_local_response(self, prompt):
        max_prompt_length = 2048  # Adjust based on model's max input length
        if len(prompt) > max_prompt_length:
            prompt = prompt[:max_prompt_length]
        response = text_gen_pipeline(prompt, max_new_tokens=256, do_sample=True, temperature=0.7)
        return response[0]['generated_text']
    
    @timeit_async
    async def answer_question(self, question: str) -> str:
        """Answer the question based on context from Qdrant."""
        try:
            context = self.get_context_from_qdrant(question)
            prompt = (
                f"Bạn là một trợ lý thông minh, hãy trả lời câu hỏi sau dựa trên ngữ cảnh:\n\n"
                f"Ngữ cảnh:\n{context}\n\n"
                f"Câu hỏi: {question}\n\n"
            )
            return self.generate_local_response(prompt)
        except Exception as e:
            return f"❌ Error: {e}"

# Typing simulation
async def typing_simulation(text, delay=0.005):
    """Simulate typing effect."""
    for char in text:
        print(char, end='', flush=True)
        await asyncio.sleep(delay)
    print()  # New line after typing


# Text to speech using Gemini
@timeit_sync
def text_to_speech_gemini(text, filename):
    """Convert text to speech using Gemini."""
    def wave_file(filename, pcm, channels=1, rate=24000, sample_width=2):
        with wave.open(filename, "wb") as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(sample_width)
            wf.setframerate(rate)
            wf.writeframes(pcm)

    client = genai.Client(api_key=GEMINI_API_KEY)

    response = client.models.generate_content(
        model="gemini-2.5-flash-preview-tts",
        contents=f"Say cheerfully:{text}!",
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name="Kore", # Choose a voice from the available options
                    )
                )
            ),
        )
    )

    data = response.candidates[0].content.parts[0].inline_data.data
    wave_file(filename, data)  # Saves the file to current directory
    print(f"TTS saved to {filename}")

# Main function to run the demo
async def main():
    # Record audio
    audio_filename = "src/demo/demo_audio_input.wav"

    # Transcribe audio using PhoWhisper
    print("🎤 Đang chuyển đổi giọng nói thành văn bản...")
    transcription = transcribe_audio_pho(audio_filename)
    print("Speech to text (PhoWhisper):", transcription)

    # Initialize chatbot
    print("🤖 Trợ lý thông minh đang trả lời câu hỏi...")
    chatbot = SmartChabot(qdrant_client, collection_name, embedding_model)
    question = transcription
    
    await asyncio.sleep(1)  # Simulate processing time

    # Get answer from chatbot
    response = await chatbot.answer_question(question)

    print()

    # Simulate typing effect for the response
    await typing_simulation(response)

    # Convert response to speech using Gemini
    print("🔊 Đang chuyển đổi văn bản thành giọng nói...")
    tts_filename = "src/demo/demo_tts_output.wav"
    text_to_speech_gemini(response, tts_filename)

    # # Play the TTS output (optional)
    # os.system(f"start {tts_filename}")  # Uncomment to play the audio file

if __name__ == "__main__":
    asyncio.run(main())

    



