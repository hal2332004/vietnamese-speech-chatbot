# import sounddevice as sd
from scipy.io.wavfile import write
from transformers import pipeline
import asyncio
import os
# from playsound import playsound
import librosa
# import soundfile as sf
import torch
import time
from functools import wraps
import warnings

secret_key = os.getenv("SECRET_KEY")

warnings.filterwarnings("ignore")

def timeit(module_name=""):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            result = func(*args, **kwargs)
            end = time.time()
            duration = end - start
            print(f"⏱️ [{module_name}] hoàn thành trong {duration:.2f} giây.")
            return result
        return wrapper
    return decorator

# def record_audio_local(filename="audio.wav", duration=10, samplerate=44100):
#     print("Start recording...")
#     recording = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype='int16')
#     sd.wait()
#     write(filename, samplerate, recording)
#     print(f"Recording saved to {filename}")

# STT using Google Gemini API
def gemini_stt(audio_path: str, secret_key: str = None):
    from google import genai
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
    def __init__(self, qdrant_client, collection_name, embedding_model, model, tokenizer, gemini_model="models/gemini-2.0-flash-exp"):
        self.qdrant_client = qdrant_client
        self.collection_name = collection_name
        
        # Move embedding model to CUDA if available
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.embedding_model = embedding_model.to(self.device)
        print(f"📢 Embedding model running on: {self.device}")
        
        self.gemini_model = gemini_model
        self.model = model
        self.tokenizer = tokenizer

    def get_context_from_qdrant(self, question, k=3):
        # Ensure input is on the same device as the model
        with torch.amp.autocast(device_type='cuda'):
            embedding = self.embedding_model.encode(
                f"Tài liệu để truy xuất: {question}",
                convert_to_tensor=True,
                device=self.device
            ).cpu().numpy().tolist()  # Convert back to CPU for Qdrant
            
        response = self.qdrant_client.search( 
            collection_name=self.collection_name,
            query_vector=embedding, 
            limit=k,
            with_payload=True
        )
        context = "\n".join([point.payload.get("văn bản", "") for point in response])
        return context

    async def local_answer_question(self, question: str) -> str:
        try:
            context = self.get_context_from_qdrant(question)
            prompt = (
                f"Bạn là một trợ lý thông minh và có tính hài hước, hãy trả lời câu hỏi sau dựa trên ngữ cảnh.\n"
                f"Câu hỏi: {question}\n\n"
                f"- Ngữ cảnh truy xuất từ cơ sở dữ liệu:\n{context}\n\n"
                f"Trả lời câu hỏi một cách chi tiết và đầy đủ. Sử dụng ngôn ngữ thuần Việt, "
                f"không chứa các ký tự đặc biệt, không dùng định dạng Markdown hay các ký hiệu như **, *, `, ~, _, #, >, hoặc các dấu câu lặp lại.\n"
                f"Câu trả lời chỉ là văn bản thuần, dễ đọc, phù hợp để sử dụng trong Text-to-Speech.\n"
                f"Hãy đảm bảo giải thích rõ ràng và cung cấp thêm thông tin hữu ích nếu có.\n"
            )

            inputs = self.tokenizer(prompt, return_tensors="pt").to("cuda")
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=512,  # Increased from 180 to 512
                min_new_tokens=100,  # Add minimum tokens to ensure longer responses
                do_sample=True,
                temperature=0.7,    # Adjust temperature for more natural responses
                top_p=0.92,         # Slightly increased for more variety
                top_k=50,          # Increased from 10 to 50 for more diverse vocabulary
                repetition_penalty=1.2  # Add repetition penalty to avoid repetitive text
            )
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            return response.strip()
        except Exception as e:
            return f"❌ Error: {e}"        
    
    async def gemini_answer_question(self, question: str) -> str:
        import google.generativeai as genai
        genai.configure(api_key=secret_key)
        
        try:
            context = self.get_context_from_qdrant(question)
            prompt = (
                f"Bạn là một trợ lý thông minh và có tính hài hước, hãy trả lời câu hỏi sau dựa trên ngữ cảnh.\n"
                f"- Ngữ cảnh truy xuất từ cơ sở dữ liệu:\n{context}\n\n"
                f"Yêu cầu:\n"
                f"1. Trả lời câu hỏi một cách chi tiết và đầy đủ\n"
                f"2. Giải thích rõ ràng và đưa ra ví dụ cụ thể nếu cần\n"
                f"3. Cung cấp thêm thông tin hữu ích liên quan\n"
                f"4. Sử dụng ngôn ngữ thuần Việt, tự nhiên và dễ hiểu\n"
                f"5. Không sử dụng ký tự đặc biệt hoặc định dạng markdown\n"
                f"6. Đảm bảo câu trả lời dễ đọc, phù hợp để sử dụng trong Text-to-Speech\n"
                f"7. Không chứa các ký tự đặc biệt, không dùng định dạng Markdown hay các ký hiệu như **, *, `, ~, _, #, >, hoặc các dấu câu lặp lại.\n\n"
                f"Câu hỏi: {question}\n\n"
            )

            model = genai.GenerativeModel(self.gemini_model)
            
            # Configure generation parameters
            generation_config = {
                "temperature": 0.7,
                "top_p": 0.92,
                "top_k": 50,
                "max_output_tokens": 1024,  # Increased token limit
            }
            
            response = model.generate_content(
                prompt,
                generation_config=generation_config
            )
            return response.text.strip()
        except Exception as e:
            return f"❌ Error: {e}"

def print_gemini_api_remaining_calls(project_id, quota_metric="serving_requests_per_day"):
    """
    Print out the remaining Gemini API calls for today.
    Args:
        project_id (str): Your Google Cloud project ID.
        quota_metric (str): The quota metric to check. Default is 'serving_requests_per_day'.
    """
    from google.cloud import monitoring_v3
    import datetime

    client = monitoring_v3.MetricServiceClient()
    project_name = f"projects/{project_id}"

    # The metric type for Gemini API quota (may need to adjust for your use case)
    metric_type = f"serving.googleapis.com/{quota_metric}"

    now = datetime.datetime.utcnow()
    interval = monitoring_v3.TimeInterval(
        end_time=now,
        start_time=now - datetime.timedelta(days=1)
    )

    results = client.list_time_series(
        request={
            "name": project_name,
            "filter": f'metric.type = "{metric_type}"',
            "interval": interval,
            "view": monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL,
        }
    )

    for result in results:
        # The quota limit and usage are in the resource labels or points
        points = result.points
        if points:
            used = points[0].value.int64_value
            limit = int(result.metric.labels.get("quota_limit", 0))
            remaining = limit - used
            print(f"Gemini API calls used today: {used}")
            print(f"Gemini API daily quota: {limit}")
            print(f"Gemini API calls remaining today: {remaining}")
            return remaining
    print("No quota usage data found for Gemini API.")
    return None
