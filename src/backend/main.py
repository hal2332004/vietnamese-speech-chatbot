from qdrant_client import QdrantClient
import asyncio
import google.generativeai as genai
from sentence_transformers import SentenceTransformer
import time
import os
from dotenv import load_dotenv
from utils import record_audio_local, transcribe_audio_pho, gemini_stt, text_to_speech_vietnamese

os.environ["TRANSFORMERS_NO_TF"] = "1"

secret_key = os.getenv("SECRET_KEY")
genai.configure(api_key=secret_key)

model = SentenceTransformer('VoVanPhuc/sup-SimCSE-VietNamese-phobert-base')

qdrant_client = QdrantClient(
    url="http://localhost:6333",  # Địa chỉ Qdrant server
    prefer_grpc=False,  # Sử dụng HTTP thay vì gRPC
)


collection_name = "syllabus_embeddings"

total_subjects = qdrant_client.count(
    collection_name=collection_name,
    exact=True  
).count

class SmartChabot:
    def __init__(self, qdrant_client, collection_name, model, gemini_model="models/gemini-2.0-flash-exp"):
        self.qdrant_client = qdrant_client
        self.collection_name = collection_name
        self.model = model
        self.gemini_model = gemini_model

    def get_context_from_qdrant(self, question, k=5):
        """ Lấy ngữ cảnh từ Qdrant dựa trên câu hỏi """
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
        """Trả lời câu hỏi dựa trên ngữ cảnh từ Qdrant."""
        try:
            context = self.get_context_from_qdrant(question)
            prompt = (
                f"Bạn là một trợ lý thông minh, hãy trả lời câu hỏi sau dựa trên ngữ cảnh.\n"
                f"- Tổng số môn học đã lưu: {total_subjects}\n"
                f"- Ngữ cảnh truy xuất từ cơ sở dữ liệu:\n{context}\n\n"
                f"Câu hỏi: {question}\n\n"
            )

            model = genai.GenerativeModel(self.gemini_model)
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return f"❌ Error: {e}"
        
async def simulate_typing(text: str):
    """Mô phỏng hiệu ứng gõ chữ."""
    for char in text:
        print(char, end='', flush=True)
        await asyncio.sleep(0.005)  # Thời gian giữa các ký tự
    print()  # Xuống dòng sau khi hoàn thành

async def main():
    chatbot = SmartChabot(qdrant_client, collection_name, model)
    question = "Tôi muốn biết thêm về môn học Lập trình Python. Bạn có thể cung cấp thông tin chi tiết không?"

    # record_audio_local(filename="my_recording.wav", duration=10)
    # question = transcribe_audio_pho("my_recording.wav")

    # question, tokens = gemini_stt("my_recording.wav")
    # print(f"Tokens sử dụng: {tokens}")
    # print(f"Câu hỏi đã nhận: {question}")   

    print("🤖 Trợ lý thông minh đang trả lời câu hỏi...")
    await asyncio.sleep(1)  

    start = time.time()
    response = await chatbot.answer_question(question)
    end = time.time()
    # await simulate_typing(response)
    print(response)
    text_to_speech_vietnamese(response)
    print(f"\n⏱️ Thời gian trả lời: {end - start:.2f} giây")

if __name__ == "__main__":
    asyncio.run(main())