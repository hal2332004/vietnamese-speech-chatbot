import os
from dotenv import load_dotenv
from utils import gemini_stt, print_gemini_api_remaining_calls

load_dotenv()
secret_key = os.getenv("SECRET_KEY")
question, tokens = gemini_stt("my_recording.mp3", secret_key=secret_key)
print(f"Tokens sử dụng: {tokens}")
print(f"Câu hỏi đã nhận: {question}")   
# print_gemini_api_remaining_calls("gen-lang-client-0955753316")