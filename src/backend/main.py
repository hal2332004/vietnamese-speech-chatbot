from qdrant_client import QdrantClient
import asyncio
import google.generativeai as genai
from sentence_transformers import SentenceTransformer
import time
import os
from dotenv import load_dotenv
from utils import record_audio_local, transcribe_audio_pho, gemini_stt, text_to_speech_vietnamese, SmartChabot
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from huggingface_hub import login

async def main():
    secret_key = os.getenv("SECRET_KEY")
    token_key = os.getenv("HUGGINGFACE_TOKEN")
    os.environ["HF_TOKEN"] = token_key
    os.environ["TRANSFORMERS_NO_TF"] = "1"
    genai.configure(api_key=secret_key)
    quantization_config = BitsAndBytesConfig(load_in_4bit=True)

    embedding_model = SentenceTransformer('VoVanPhuc/sup-SimCSE-VietNamese-phobert-base')
    tokenizer = AutoTokenizer.from_pretrained("google/gemma-2b", token=token_key)
    model = AutoModelForCausalLM.from_pretrained("google/gemma-2b", quantization_config=quantization_config, device_map="auto", token=token_key)

    qdrant_client = QdrantClient(
        url="http://localhost:6333",  # Địa chỉ Qdrant server
        prefer_grpc=False,  # Sử dụng HTTP thay vì gRPC
    )

    collection_name = "syllabus_embeddings"

    total_subjects = qdrant_client.count(
        collection_name=collection_name,
        exact=True  
    ).count

    start = time.time()
    chatbot = SmartChabot(qdrant_client, collection_name, embedding_model, model=model, tokenizer=tokenizer)
    question = "Tôi muốn biết thêm về môn học Lập trình Python. Bạn có thể cung cấp thông tin chi tiết không?"

    # record_audio_local(filename="my_recording.wav", duration=10)
    # question = transcribe_audio_pho("my_recording.wav")

    question, tokens = gemini_stt("my_recording.wav", secret_key=secret_key)
    print(f"Tokens sử dụng: {tokens}")
    print(f"Câu hỏi đã nhận: {question}")   

    print("🤖 Trợ lý thông minh đang trả lời câu hỏi...")
    await asyncio.sleep(1)  

    response = await chatbot.answer_question(question)
    # await simulate_typing(response)
    print(response)
    text_to_speech_vietnamese(response)
    end = time.time()
    print(f"\n⏱️ Thời gian trả lời: {end - start:.2f} giây")

if __name__ == "__main__":
    asyncio.run(main())                                                   