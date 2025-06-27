from qdrant_client import QdrantClient
import asyncio
# import google.generativeai as genai
from sentence_transformers import SentenceTransformer
import time
import os
from dotenv import load_dotenv
from utils import SmartChabot
import torch
import argparse
load_dotenv()

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--llama_cpp', action='store_true', help='Dùng llama.cpp server')
    args = parser.parse_args()
    
    QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
    QDRANT_HOST = os.getenv("QDRANT_HOST")

    embedding_model = SentenceTransformer('Alibaba-NLP/gte-multilingual-base', trust_remote_code=True)

    qdrant_client = QdrantClient(
        api_key=QDRANT_API_KEY, 
        url=QDRANT_HOST, 
        https=True,
    )

    start = time.time()
    collection_name = "syllabus_embeddings_gte"
    chatbot = SmartChabot(qdrant_client, collection_name, embedding_model)

    question = "Mô tả trường đại học FPT"

    print("🤖 Trợ lý thông minh đang trả lời câu hỏi...")

    if args.llama_cpp:
        response = await chatbot.llama_cpp_answer_question(question)

    print(response)
    end = time.time()
    print(f"\n⏱️ Thời gian trả lời: {end - start:.2f} giây")

if __name__ == "__main__":
    asyncio.run(main())