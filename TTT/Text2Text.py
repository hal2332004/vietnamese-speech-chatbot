from qdrant_client import QdrantClient
import asyncio
import google.generativeai as genai
# from chatbot.DataCollection.crawl_data import collection_name, qdrant_client
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
import os

# Tải biến môi trường từ file .env
load_dotenv()
# Lấy API key từ biến môi trường
API_KEY = os.getenv("GEMINI_API_KEY")

# Khởi tạo kết nối với Qdrant
qdrant_client = QdrantClient(
    url="http://localhost:6333",  # Địa chỉ Qdrant server
    prefer_grpc=False,  # Sử dụng HTTP thay vì gRPC
)
collection_name = "syllabus_embeddings"


# --- Khởi tạo mô hình ---
model = SentenceTransformer("intfloat/multilingual-e5-large-instruct")

# Khởi tạo Google Generative AI
genai.configure(api_key=API_KEY)  # Thay thế bằng API key của bạn

# --- Định nghĩa Chatbot ---
class SmartChabot:
    def __init__(self, qdrant_client, collection_name, model, gemini_model="models/gemini-2.0-flash-exp"):
        self.qdrant_client = qdrant_client
        self.collection_name = collection_name
        self.model = model
        self.gemini_model = gemini_model

    def get_context_from_qdrant(self, question, k=29):
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
                f"Bạn là một trợ lý thông minh, hãy trả lời câu hỏi sau dựa trên ngữ cảnh:\n\n"
                f"Ngữ cảnh:\n{context}\n\n"
                f"Câu hỏi: {question}\n\n"
            )

            model = genai.GenerativeModel(self.gemini_model)
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return f"❌ Error: {e}"
        
# --- Hiệu ứng gõ chữ ---
async def simulate_typing(text: str):
    """Mô phỏng hiệu ứng gõ chữ."""
    for char in text:
        print(char, end='', flush=True)
        await asyncio.sleep(0.005)  # Thời gian giữa các ký tự
    print()  # Xuống dòng sau khi hoàn thành

# --- Hàm chính ---
async def main():
    """Hàm chính để chạy chatbot."""
    # Khởi tạo mô hình và chatbot
    chatbot = SmartChabot(qdrant_client, collection_name, model)
    question = "Cho tôi thông tin về môn học sâu"
    print("🤖 Trợ lý thông minh đang trả lời câu hỏi...")

    await asyncio.sleep(1)  # Giả lập thời gian xử lý

    response = await chatbot.answer_question(question)

    print()

    await simulate_typing(response)

if __name__ == "__main__":
    asyncio.run(main())