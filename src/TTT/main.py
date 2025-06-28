from qdrant_client import QdrantClient
import asyncio
from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
import os
from dotenv import load_dotenv
from smartbot import SmartChabot
import torch
import argparse
import uvicorn

# Initialize FastAPI app
app = FastAPI()
load_dotenv()

# Initialize models and clients at startup
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_HOST = os.getenv("QDRANT_HOST")
embedding_model = SentenceTransformer('Alibaba-NLP/gte-multilingual-base', trust_remote_code=True)
qdrant_client = QdrantClient(
    api_key=QDRANT_API_KEY, 
    url=QDRANT_HOST, 
    https=True,
)
collection_name = "syllabus_embeddings_gte"
chatbot = SmartChabot(qdrant_client, collection_name, embedding_model)

class AskRequest(BaseModel):
    question: str

@app.post("/ask")
async def ask(request: AskRequest):
    response = await chatbot.llama_cpp_answer_question(request.question)
    response = response.replace("**", "")
    return {"answer": response}

@app.post("/ask_stream")
async def ask_stream(request: AskRequest):
    async def word_stream():
        response = await chatbot.llama_cpp_answer_question(request.question)
        response = response.replace("**", "")
        for word in response.split():
            yield word + " "
            await asyncio.sleep(0.05)  # simulate streaming
    return StreamingResponse(word_stream(), media_type="text/plain")


if __name__ == '__main__':
    uvicorn.run(
        "main:app", 
        host="0.0.0.0",
        port=12346,
        reload=True,
        log_level="info"
    )
# async def main():
#     parser = argparse.ArgumentParser()
#     parser.add_argument('--llama_cpp', action='store_true', help='Dùng llama.cpp server')
#     args = parser.parse_args()
    
#     QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
#     QDRANT_HOST = os.getenv("QDRANT_HOST")

#     embedding_model = SentenceTransformer('Alibaba-NLP/gte-multilingual-base', trust_remote_code=True)

#     qdrant_client = QdrantClient(
#         api_key=QDRANT_API_KEY, 
#         url=QDRANT_HOST, 
#         https=True,
#     )

#     collection_name = "syllabus_embeddings_gte"
#     chatbot = SmartChabot(qdrant_client, collection_name, embedding_model)

#     question = "Logo của FPT có ý nghĩa gì"


#     if args.llama_cpp:
#         print("🤖 Trợ lý thông minh đang trả lời câu hỏi...")
#         response = await chatbot.llama_cpp_answer_question(question)
#         response = response.replace("**", "")

#     print(response)

# if __name__ == "__main__":
#     asyncio.run(main())