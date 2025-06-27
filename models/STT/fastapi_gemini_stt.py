import os
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
import tempfile
import shutil
import uvicorn
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

app = FastAPI()

# Thêm CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # hoặc chỉ định domain cụ thể
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ALLOWED_MODELS = [
    "gemini-2.0-flash-lite",
    "gemini-2.0-flash",
    "gemini-2.5-flash-lite-preview-06-17"
]

def gemini_stt(audio_path: str, secret_key: str = None, model: str = "gemini-2.5-flash-lite-preview-06-17"):
    from google import genai
    client = genai.Client(api_key=secret_key)
    uploaded_file = client.files.upload(file=audio_path)

    response = client.models.generate_content(
        model=model,
        contents=[
            "Chuyển âm thanh sau thành văn bản tiếng Việt, chỉ trả lại phần nội dung lời nói. Không thêm tiêu đề, mô tả hay giải thích nào khác.",
            uploaded_file
        ]
    )

    token_info = client.models.count_tokens(
        model=model,
        contents=[uploaded_file]
    )

    return response.text, token_info

from fastapi import Form

@app.post("/stt")
async def stt_api(
    file: UploadFile = File(...),
    model: str = Form("gemini-2.5-flash-lite-preview-06-17")
):
    secret_key = os.getenv("GEMINI_API_KEY")
    if not secret_key:
        return JSONResponse(status_code=500, content={"error": "SECRET_KEY not set"})
    if model not in ALLOWED_MODELS:
        return JSONResponse(status_code=400, content={"error": "Model không hợp lệ"})

    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        text, token_info = gemini_stt(tmp_path, secret_key, model)
        return {"text": text, "token_info": token_info}
    finally:
        os.remove(tmp_path)

if __name__ == '__main__':
    uvicorn.run(
        "fastapi_gemini_stt:app", 
        host="0.0.0.0",
        port=12345,
        reload=True,
        log_level="info"
    )