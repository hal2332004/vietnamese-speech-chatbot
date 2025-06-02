import sounddevice as sd
from scipy.io.wavfile import write
import os
from transformers import pipeline
from qdrant_client import QdrantClient
from dotenv import load_dotenv
import asyncio
import google.generativeai as genai1
from sentence_transformers import SentenceTransformer
import wave
from google import genai
from google.genai import types

# Load environment variables from .env file
load_dotenv()
# Get API key from environment variable
API_KEY = os.getenv("GEMINI_API_KEY")
# Initialize Google Generative AI
genai1.configure(api_key=API_KEY)  # Replace with your API key

# Initialize Qdrant client
qdrant_client = QdrantClient(
    url="http://localhost:6333",  # Qdrant server address
    prefer_grpc=False,  # Use HTTP instead of gRPC
)

# Collection name for Qdrant
collection_name = "syllabus_embeddings"

# Initialize SentenceTransformer model
model = SentenceTransformer("intfloat/multilingual-e5-large-instruct")

# Ensure ffmpeg is in the PATH for audio processing
os.environ["PATH"] += os.pathsep + "C:\\ProgramData\\chocolatey\\lib\\ffmpeg\\tools\\ffmpeg\\bin"

# Record audio and save the file WAV
def record_audio_local(filename, duration=10, samplerate=44100):
    print("Start recording...")
    recording = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype='int16')
    sd.wait()
    write(filename, samplerate, recording)
    print(f"Recording saved to {filename}")


# PhoWhisper transcription
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
    
    async def answer_question(self, question: str) -> str:
        """Answer the question based on context from Qdrant."""
        try:
            context = self.get_context_from_qdrant(question)
            prompt = (
                f"Bạn là một trợ lý thông minh, hãy trả lời câu hỏi sau dựa trên ngữ cảnh:\n\n"
                f"Ngữ cảnh:\n{context}\n\n"
                f"Câu hỏi: {question}\n\n"
            )

            model = genai1.GenerativeModel(self.gemini_model)
            response = model.generate_content(prompt)
            return response.text.strip()
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
def text_to_speech_gemini(text, filename):
    """Convert text to speech using Gemini."""
    def wave_file(filename, pcm, channels=1, rate=24000, sample_width=2):
        with wave.open(filename, "wb") as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(sample_width)
            wf.setframerate(rate)
            wf.writeframes(pcm)

    client = genai.Client(api_key=API_KEY)

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
    audio_filename = "E:/CN_AI/SU2025/DAT301m/demo/demo_audio_input.wav"
    record_audio_local(audio_filename, duration=5)

    # Transcribe audio using PhoWhisper
    transcription = transcribe_audio_pho(audio_filename)
    print("Speech to text (PhoWhisper):", transcription)

    # Initialize chatbot
    chatbot = SmartChabot(qdrant_client, collection_name, model)
    question = transcription
    print("🤖 Trợ lý thông minh đang trả lời câu hỏi...")
    
    await asyncio.sleep(1)  # Simulate processing time

    # Get answer from chatbot
    response = await chatbot.answer_question(question)

    print()

    # Simulate typing effect for the response
    await typing_simulation(response)

    # Convert response to speech using Gemini
    tts_filename = "E:/CN_AI/SU2025/DAT301m/demo/demo_tts_output.wav"
    text_to_speech_gemini(response, tts_filename)

    # Play the TTS output (optional)
    os.system(f"start {tts_filename}")  # Uncomment to play the audio file

if __name__ == "__main__":
    asyncio.run(main())

    



