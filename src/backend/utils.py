import sounddevice as sd
from scipy.io.wavfile import write
from transformers import pipeline
import asyncio
from gtts import gTTS
import os
from playsound import playsound
import librosa
import soundfile as sf
import torch
secret_key = os.getenv("SECRET_KEY")

def text_to_speech_vietnamese(text, model="gtts", speed=1.5):
    if model == "gtts":
        tts = gTTS(text=text, lang='vi')
        filename = "tts_output.mp3"
        tts.save(filename)
        
        # Load and speed up audio using librosa
        y, sr = librosa.load(filename)
        # Speed up by reducing duration (1.5x speed means duration is reduced to 2/3)
        y_fast = librosa.effects.time_stretch(y=y, rate=speed)
        
        # Save the modified audio
        sf.write(filename, y_fast, sr)
        
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
def gemini_stt(audio_path: str, secret_key: str = None):
    from google import genai
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


class SmartChabot:
    def __init__(self, qdrant_client, collection_name, embedding_model, model, tokenizer, gemini_model="models/gemini-2.0-flash-exp"):
        self.qdrant_client = qdrant_client
        self.collection_name = collection_name
        self.embedding_model = embedding_model
        self.gemini_model = gemini_model
        self.model = model
        self.tokenizer = tokenizer

    def get_context_from_qdrant(self, question, k=3):
        embedding = self.embedding_model.encode(f"Tài liệu để truy xuất: {question}").tolist()
        response = self.qdrant_client.search( 
            collection_name=self.collection_name,
            query_vector=embedding, 
            limit=k,
            with_payload=True
        )
        context = "\n".join([point.payload.get("văn bản", "") for point in response])
        return context

    async def local_answer_question(self, question: str) -> str:
        try:
            context = self.get_context_from_qdrant(question)
            prompt = (
                f"Bạn là một trợ lý thông minh và có tính hài hước, hãy trả lời câu hỏi sau dựa trên ngữ cảnh.\n"
                f"Câu hỏi: {question}\n\n"
                f"- Ngữ cảnh truy xuất từ cơ sở dữ liệu:\n{context}\n\n"
                f"Trả lời câu hỏi một cách thật tự nhiên, sử dụng ngôn ngữ thuần Việt, "
                f"không chứa các ký tự đặc biệt, không dùng định dạng Markdown hay các ký hiệu như **, *, `, ~, _, #, >, hoặc các dấu câu lặp lại.\n"
                f"Câu trả lời chỉ là văn bản thuần, dễ đọc, phù hợp để sử dụng trong Text-to-Speech.\n"
            )

            inputs = self.tokenizer(prompt, return_tensors="pt").to("cuda")
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=180,  # Changed from max_length to max_new_tokens
                do_sample=True,
                top_p=0.9,
                top_k=10
            )
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            return response.strip()
        except Exception as e:
            return f"❌ Error: {e}"        
    
    async def gemini_answer_question(self, question: str) -> str:
        import google.generativeai as genai
        genai.configure(api_key=secret_key)
        
        try:
            context = self.get_context_from_qdrant(question)
            prompt = (
                f"Bạn là một trợ lý thông minh và có tính hài hước, hãy trả lời câu hỏi sau dựa trên ngữ cảnh.\n"
                f"- Ngữ cảnh truy xuất từ cơ sở dữ liệu:\n{context}\n\n"
                f"Trả lời câu hỏi một cách thật tự nhiên, sử dụng ngôn ngữ thuần Việt, "
                f"không chứa các ký tự đặc biệt, không dùng định dạng Markdown hay các ký hiệu như **, *, `, ~, _, #, >, hoặc các dấu câu lặp lại.\n"
                f"Câu trả lời chỉ là văn bản thuần, dễ đọc, phù hợp để sử dụng trong Text-to-Speech.\n"
                f"Câu hỏi: {question}\n\n"
            )

            model = genai.GenerativeModel(self.gemini_model)
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return f"❌ Error: {e}"


    
    # async def is_question_related_to_syllabus(self, question: str) -> bool:
    #     import google.generativeai as genai
    #     genai.configure(api_key=secret_key)

    #     prompt = (
    #         f"Hãy đọc câu hỏi sau và xác định xem nó có liên quan đến các môn học, chương trình học hoặc nội dung giảng dạy hay không.\n"
    #         f"Câu hỏi: \"{question}\"\n"
    #         f"Trả lời \"có\" nếu có liên quan đến giáo trình hoặc môn học, còn lại thì trả lời \"không\"."
    #     )

    #     try:
    #         model = genai.GenerativeModel(self.gemini_model)
    #         response = model.generate_content(prompt)
    #         answer = response.text.lower().strip()
    #         return "có" in answer
    #     except Exception as e:
    #         print(f"Lỗi khi phân loại câu hỏi: {e}")
    #         return False
        
    # async def answer_question2(self, question: str) -> str:
    #     is_related = await self.is_question_related_to_syllabus(question)

    #     if is_related:
    #         context = self.get_context_from_qdrant(question)
    #         prompt = (
    #             f"Bạn là một trợ lý người Việt Nam thông minh và thân thiện, hãy trả lời câu hỏi sau dựa trên ngữ cảnh.\n"
    #             f"- Ngữ cảnh truy xuất từ cơ sở dữ liệu:\n{context}\n\n"
    #             f"Trả lời câu hỏi một cách thật tự nhiên, sử dụng ngôn ngữ thuần Việt, "
    #             f"không chứa các ký tự đặc biệt, không dùng định dạng Markdown hay các ký hiệu như **, *, `, ~, _, #, >, hoặc các dấu câu lặp lại.\n"
    #             f"Câu trả lời chỉ là văn bản thuần, dễ đọc, phù hợp để sử dụng trong Text-to-Speech.\n"
    #             f"Câu hỏi: {question}\n\n"
    #         )
    #     else:
    #         prompt = (
    #             f"Bạn là một trợ lý người Việt Nam thông minh và thân thiện. Hãy trả lời câu hỏi sau bằng ngôn ngữ thuần Việt, tự nhiên và dễ hiểu:\n\n"
    #             f"{question}"
    #         )

    #     try:
    #         import google.generativeai as genai
    #         genai.configure(api_key=secret_key)
    #         model = genai.GenerativeModel(self.gemini_model)
    #         response = model.generate_content(prompt)
    #         return response.text.strip()
    #     except Exception as e:
    #         return f"❌ Lỗi khi sinh câu trả lời: {e}"

