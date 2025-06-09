import sounddevice as sd
from scipy.io.wavfile import write
from transformers import pipeline
from google import genai
import asyncio
from gtts import gTTS
import os
from playsound import playsound

def text_to_speech_vietnamese(text, model="gtts"):
    if model == "gtts":
        tts = gTTS(text=text, lang='vi')
        filename = "tts_output.mp3"
        tts.save(filename)
        playsound(filename)
        os.remove(filename)
    else:
        raise ValueError(f"Unsupported TTS model: {model}")


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
    def __init__(self, qdrant_client, collection_name, embedding_model, model, tokenizer):#, gemini_model="models/gemini-2.0-flash-exp"):
        self.qdrant_client = qdrant_client
        self.collection_name = collection_name
        self.embedding_model = embedding_model
        # self.gemini_model = gemini_model
        self.model = model
        self.tokenizer = tokenizer

    def get_context_from_qdrant(self, question, k=2):
        embedding = self.embedding_model.encode(f"Tài liệu để truy xuất: {question}").tolist()
        response = self.qdrant_client.search(  # Changed from search to query_points
            collection_name=self.collection_name,
            query_vector=embedding, 
            limit=k,
            with_payload=True
        )
        context = "\n".join([point.payload.get("văn bản", "") for point in response])
        return context
    
    async def answer_question(self, question: str) -> str:
        try:
            context = self.get_context_from_qdrant(question)
            prompt = (
                f"Bạn là một trợ lý người Việt Nam thông minh và thân thiện, hãy trả lời câu hỏi sau dựa trên ngữ cảnh.\n"
                f"- Ngữ cảnh truy xuất từ cơ sở dữ liệu:\n{context}\n\n"
                f"Trả lời câu hỏi một cách thật tự nhiên, sử dụng ngôn ngữ thuần Việt và độ dài phù hợp với trong giao tiếp.\n"
                f"Câu hỏi: {question}\n\n"
            )

            inputs = self.tokenizer(prompt, return_tensors="pt").to("cuda")
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=128,  # Changed from max_length to max_new_tokens
                do_sample=True,
                top_p=0.9,
                top_k=10
            )
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            return response.strip()
        except Exception as e:
            return f"❌ Error: {e}"
    

    # async def answer_question(self, question: str) -> str:
    #     try:
    #         context = self.get_context_from_qdrant(question)
    #         prompt = (
    #             f"Bạn là một trợ lý người Việt Nam thông minh và thân thiện, hãy trả lời câu hỏi sau dựa trên ngữ cảnh.\n"
    #             f"- Tổng số môn học đã lưu: {total_subjects}\n"
    #             f"- Ngữ cảnh truy xuất từ cơ sở dữ liệu:\n{context}\n\n"
    #             f"Trả lời câu hỏi một cách thật tự nhiên, sử dụng ngôn ngữ thuần Việt, "
    #             f"không chứa các ký tự đặc biệt, không dùng định dạng Markdown hay các ký hiệu như **, *, `, ~, _, #, >, hoặc các dấu câu lặp lại.\n"
    #             f"Câu trả lời chỉ là văn bản thuần, dễ đọc, phù hợp để sử dụng trong Text-to-Speech.\n"
    #             f"Câu hỏi: {question}\n\n"
    #         )

    #         model = genai.GenerativeModel(self.gemini_model)
    #         response = modelgenerate_content.(prompt)
    #         return response.text.strip()
    #     except Exception as e:
    #         return f"❌ Error: {e}"

