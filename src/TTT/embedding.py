from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance
import pandas as pd
import os
from dotenv import load_dotenv
load_dotenv()

QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_HOST = os.getenv("QDRANT_HOST")

# model = SentenceTransformer("intfloat/multilingual-e5-large-instruct")
# print("Model size embedding:", model.get_sentence_embedding_dimension())

model = SentenceTransformer("Alibaba-NLP/gte-multilingual-base", trust_remote_code=True)
print("Model size embedding:", model.get_sentence_embedding_dimension())

qdrant_client = QdrantClient(
    api_key = QDRANT_API_KEY, 
    url = QDRANT_HOST, 
    https = True,  
)
collection_name = "syllabus_embeddings_gte"

# Xóa collection nếu đã tồn tại
if qdrant_client.collection_exists(collection_name):
    qdrant_client.delete_collection(collection_name)
    print(f"❌ Collection '{collection_name}' đã tồn tại và đã bị xóa.")

# Tạo collection nếu chưa tồn tại
if not qdrant_client.collection_exists(collection_name):
    qdrant_client.create_collection(
        collection_name,
        vectors_config=VectorParams(size=model.get_sentence_embedding_dimension(), distance=Distance.COSINE),
    )
    print(f"✅ Collection '{collection_name}' created.")

csv_path = "../../data/Giáo trình môn học FPT 2 - syllabus_data_format.csv"
df = pd.read_csv(csv_path)
print(df.head())

if "Văn bản" not in df.columns:
    raise ValueError("CSV không có cột 'Văn bản'.")

# Lấy danh sách văn bản
texts = df["Văn bản"].astype(str).tolist()

# Tính embedding cho từng văn bản
embeddings = model.encode(texts, show_progress_bar=True)

# Chuẩn bị dữ liệu để lưu lên Qdrant
points = [
    PointStruct(
        id=i,
        vector=embeddings[i],
        payload={"text": texts[i]}
    )
    for i in range(len(texts))
]

# Lưu embedding lên Qdrant
qdrant_client.upsert(
    collection_name=collection_name,
    points=points
)

print(f"✅ Đã lưu {len(points)} embeddings lên Qdrant Cloud.")

