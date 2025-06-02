from google import genai
from google.genai import types
import wave
from dotenv import load_dotenv
import os

# Tải biến môi trường từ file .env
load_dotenv()
# Lấy API key từ biến môi trường
API_KEY = os.getenv("GEMINI_API_KEY")

text = "Xin chào, tôi là một trợ lý ảo. Tôi có thể giúp gì cho bạn hôm nay?"

# Set up the wave file to save the output:
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
               voice_name='Kore',
            )
         )
      ),
   )
)

data = response.candidates[0].content.parts[0].inline_data.data

file_name="E:/CN AI/SU2025/DAT301m/TTS/tts_gemini.wav"
wave_file(file_name, data) # Saves the file to current directory