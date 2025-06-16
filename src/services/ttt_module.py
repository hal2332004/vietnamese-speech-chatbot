from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
import os
from dotenv import load_dotenv
from src.utils.time_logger import timeit
import warnings
warnings.filterwarnings("ignore")

# Load environment variables from .env file
load_dotenv()

# Get GEMINI API key from environment variable
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Get QDRANT API key and host from environment variables
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_HOST = os.getenv("QDRANT_HOST")

# Create pipeline for text generation using HuggingFace token
tokenizer = AutoTokenizer.from_pretrained("tiiuae/falcon-rw-1b") #token=hf_token)
model = AutoModelForCausalLM.from_pretrained("tiiuae/falcon-rw-1b") #token=hf_token)
text_gen_pipeline = pipeline("text-generation", model=model, tokenizer=tokenizer, device=0)

# Create pipeline for text generation using HuggingFace token
tokenizer = AutoTokenizer.from_pretrained("tiiuae/falcon-rw-1b") #token=hf_token)
model = AutoModelForCausalLM.from_pretrained("tiiuae/falcon-rw-1b") #token=hf_token)
text_gen_pipeline = pipeline("text-generation", model=model, tokenizer=tokenizer, device=0)


# Initialize Qdrant client for Docker 
qdrant_client = QdrantClient(
    api_key=QDRANT_API_KEY,  # Qdrant API key
    url=QDRANT_HOST,  # Qdrant server URL 
    https=True,  # Use HTTPS
)

# Collection name for Qdrant
COLLECTION_NAME = "syllabus_embeddings"

# Initialize SentenceTransformer model
embedding_model = SentenceTransformer("intfloat/multilingual-e5-large-instruct")

# Qdrant search function to retrieve context based on a question
@timeit("LLM: Qdrant Search")
def get_context(question, k=29):
    """
    Retrieve context from Qdrant based on the question.
    
    Args:
        question (str): The question to search for.
        k (int): Number of nearest neighbors to retrieve.
        
    Returns:
        list: List of contexts retrieved from Qdrant.
    """
    embedding = embedding_model.encode(f"Tài liệu để truy xuất: {question}").tolist()
    response = qdrant_client.search(
        collection_name=COLLECTION_NAME,
        query_vector=embedding,
        limit=k,
        with_payload=True
    )
    context = "\n".join([pt.payload.get("văn bản", "") for pt in response])
    return context

# Function to generate text using the LLM
@timeit("LLM: Generate Answer")
def generate_answer(question):
    """
    Generate an answer to the question using the LLM.
    
    Args:
        question (str): The question to answer.
        
    Returns:
        str: Generated answer from the LLM.
    """
    context = get_context(question)
    prompt = f"Tài liệu để truy xuất: {context}\n\nCâu hỏi: {question}\nTrả lời:"
    
    # Adjust based on model's max input length
    max_prompt_length = 2048
    if len(prompt) > max_prompt_length:
        prompt = prompt[:max_prompt_length]

    response = text_gen_pipeline(prompt, max_new_tokens=256, do_sample=True, temperature=0.7)
    answer = response[0]['generated_text'].strip()
    print("🤖 Chatbot Answer:\n", answer)
    return answer
