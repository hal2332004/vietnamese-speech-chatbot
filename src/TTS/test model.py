from llama_cpp import Llama
import torch
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"CUDA devices: {torch.cuda.device_count()}")

# Load mô hình
llm = Llama(
    model_path="ggml-vistral-7B-chat-q4_0.gguf",
    n_ctx=2048,
    n_threads=4,       # Tùy CPU bạn, có thể tăng nếu đa nhân
    n_gpu_layers=32     # Nếu dùng CPU; nếu dùng GPU có thể đặt số lớn hơn 0
)

# Chat loop
print("🤖 Chatbot sẵn sàng. Gõ 'exit' để thoát.")
while True:
    user_input = input("👤 Bạn: ")
    if user_input.lower() in ["exit", "quit"]:
        print("👋 Tạm biệt!")
        break

    output = llm.create_completion(
        prompt=f"[INST] {user_input} [/INST]",
        max_tokens=512,
        temperature=0.7,
        top_p=0.95,
        stop=["</s>"]
    )
    
    response = output["choices"][0]["text"]
    print("🤖 Bot:", response.strip())
