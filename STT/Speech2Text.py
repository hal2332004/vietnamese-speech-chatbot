from transformers import pipeline
import os
os.environ["PATH"] += os.pathsep + "C:\\ProgramData\\chocolatey\\lib\\ffmpeg\\tools\\ffmpeg\\bin"

# PhoWhisper transcription
def transcribe_audio_pho(filename="E:/CN AI/SU2025/DAT301m/STT/audio.wav"):
    pipe = pipeline("automatic-speech-recognition", model="vinai/PhoWhisper-base")
    result = pipe(filename)
    return result['text']

# Record and transcribe
text = transcribe_audio_pho("E:/CN AI/SU2025/DAT301m/STT/audio.wav")
print("Speech to text (PhoWhisper):", text)

