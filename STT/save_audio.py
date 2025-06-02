import sounddevice as sd
from scipy.io.wavfile import write

# Record audio and save the file WAV
def record_audio_local(filename="E:/CN AI/SU2025/DAT301m/STT/audio.wav", duration=10, samplerate=44100):
    print("Start recording...")
    recording = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype='int16')
    sd.wait()
    write(filename, samplerate, recording)
    print(f"Recording saved to {filename}")

if __name__ == "__main__":
    record_audio_local(duration=5)