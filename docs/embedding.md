https://huggingface.co/AITeamVN/Vietnamese_Embedding:
Vietnamese_Embedding is an embedding model fine-tuned from the BGE-M3 model (https://huggingface.co/BAAI/bge-m3) to enhance retrieval capabilities for Vietnamese.

The model was trained on approximately 300,000 triplets of queries, positive documents, and negative documents for Vietnamese.
The model was trained with a maximum sequence length of 2048.

from sentence_transformers import SentenceTransformer
import torch

model = SentenceTransformer("AITeamVN/Vietnamese_Embedding")
model.max_seq_length = 2048
sentences_1 = ["Trí tuệ nhân tạo là gì", "Lợi ích của giấc ngủ"]
sentences_2 = ["Trí tuệ nhân tạo là công nghệ giúp máy móc suy nghĩ và học hỏi như con người. Nó hoạt động bằng cách thu thập dữ liệu, nhận diện mẫu và đưa ra quyết định.", 
               "Giấc ngủ giúp cơ thể và não bộ nghỉ ngơi, hồi phục năng lượng và cải thiện trí nhớ. Ngủ đủ giấc giúp tinh thần tỉnh táo và làm việc hiệu quả hơn."]
query_embedding = model.encode(sentences_1)
doc_embeddings = model.encode(sentences_2)
similarity = query_embedding @ doc_embeddings.T
print(similarity)

'''
array([[0.66212064, 0.33066642],
       [0.25866613, 0.5865289 ]], dtype=float32)
'''


https://huggingface.co/VoVanPhuc/sup-SimCSE-VietNamese-phobert-base
SimeCSE_Vietnamese: Simple Contrastive Learning of Sentence Embeddings with Vietnamese
Pre-trained SimeCSE_Vietnamese models are the state-of-the-art of Sentence Embeddings with Vietnamese :

SimeCSE_Vietnamese pre-training approach is based on SimCSE which optimizes the SimeCSE_Vietnamese pre-training procedure for more robust performance.
SimeCSE_Vietnamese encode input sentences using a pre-trained language model such as PhoBert
SimeCSE_Vietnamese works with both unlabeled and labeled data.


https://huggingface.co/dangvantuan/vietnamese-embedding
Dataset: ViNLI-SimCSE-supervised
Dataset: XNLI-vn
Dataset: STSB-vn
Dataset: STSB-vn with generate silver sample from gold sample


https://huggingface.co/keepitreal/vietnamese-sbert
