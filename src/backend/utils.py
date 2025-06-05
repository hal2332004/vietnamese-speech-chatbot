import sounddevice as sd
from scipy.io.wavfile import write
from transformers import pipeline
from google import genai
import os 

from gtts import gTTS
import os
from playsound import playsound

def text_to_speech_vietnamese(text):
    tts = gTTS(text=text, lang='vi')
    filename = "tts_output.mp3"
    tts.save(filename)
    playsound(filename)
    os.remove(filename)


# Record audio and save the file WAV
def record_audio_local(filename="audio.wav", duration=10, samplerate=44100):
    print("Start recording...")
    recording = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype='int16')
    sd.wait()
    write(filename, samplerate, recording)
    print(f"Recording saved to {filename}")

# PhoWhisper transcription
def transcribe_audio_pho(filename="audio.wav"):
    pipe = pipeline("automatic-speech-recognition", model="vinai/PhoWhisper-small")
    result = pipe(filename)
    return result['text']

# STT using Google Gemini API
def gemini_stt(audio_path: str):
    secret_key = os.getenv("SECRET_KEY")
    if not secret_key:
        raise ValueError("SECRET_KEY chưa được đặt trong file .env")

    client = genai.Client(api_key=secret_key)

    uploaded_file = client.files.upload(file=audio_path)

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[
            "Trích xuất văn bản tiếng Việt từ audio tôi cung cấp",
            uploaded_file
        ]
    )

    print("Văn bản trích xuất:")
    print(response.text)

    token_info = client.models.count_tokens(
        model="gemini-2.0-flash",
        contents=[uploaded_file]
    )

    print("\nThông tin token:")
    print(token_info)

    return response.text, token_info

# text, tokens = gemini_stt("test-sound.wav")