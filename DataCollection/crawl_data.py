from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance
import hashlib
import pandas as pd
import os
from dotenv import load_dotenv

# Tải biến môi trường từ file .env
load_dotenv()

# Lấy Qdrant API key từ biến môi trường
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_HOST = os.getenv("QDRANT_HOST")

# Tải session đã lưu từ file
SESSION_FILE = "DataCollection\session.json"

# Khởi tạo Google Translator
translator = GoogleTranslator(source='auto', target='vi')  # Dịch sang tiếng Việt

# Khởi tạo mô hình SentenceTransformer
model = SentenceTransformer("intfloat/multilingual-e5-large-instruct")

# Khởi tạo kết nối với Qdrant
qdrant_client = QdrantClient(
    api_key = QDRANT_API_KEY, # Khóa API Qdrant
    url = QDRANT_HOST,  # Địa chỉ Qdrant server
    https = True,  # Sử dụng HTTPS
)
collection_name = "syllabus_embeddings"

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

# Hàm tạo ID duy nhất cho mỗi điểm
def url_to_id(url):
    return hashlib.md5(url.encode()).hexdigest()

# Tạo embedding và lưu vào Qdrant
def create_and_store_embedding(text: str, url: str):
    try:
        embedding_input = f"Tài liệu để truy xuất: {text}"
        embedding = model.encode(embedding_input)

        point_id = url_to_id(url)   # Tạo ID duy nhất cho điểm
        qdrant_client.upsert(
            collection_name=collection_name,
            points=[
                PointStruct(
                    id=point_id,
                    vector=embedding.tolist(),
                    payload={"url": url, "văn bản": text}
                )
            ]
        )
        print(f"📥 Đã lưu embedding với ID: {point_id}")

    except Exception as e:
        print(f"❌ Lỗi khi tạo hoặc lưu embedding: {e}")

# Dịch văn bản sử dụng Google Translator
def translate_text(text: str) -> str:
    try:
        translated = translator.translate(text)
        return translated
    except Exception as e:
        print(f"❌ Lỗi dịch: {e}")
        return text  # Trả về văn bản gốc nếu có lỗi

# Loại bỏ khoảng trắng thừa và định dạng văn bản
def clean(text: str) -> str:
    """Loại bỏ khoảng trắng thừa đầu, cuối và gom các khoảng trắng giữa."""
    return ' '.join(text.strip().split())

# Sửa đổi text trong bảng HTML cho phù hợp
def modify_table_text(text: str) -> str:
    """Sửa text Nocredit thành số lượng tín chỉ."""
    if "Nocredit" in text:
        text = text.replace("Nocredit", "Số tín chỉ")

    """Sửa Giờ liên hệ thành Giờ học."""
    if "Giờ liên hệ" in text:   
        text = text.replace("Giờ liên hệ", "Giờ học")

    """Sửa ISAPPRIVE thành Được chấp thuận."""
    if "ISAPPRIVE" in text:
        text = text.replace("ISAPPRIVE", "Được chấp thuận")

    """Sửa Đúng vậy thành Có."""
    if "Đúng vậy" in text:
        text = text.replace("Đúng vậy", "Có")

    """Sửa Minavgmarktopass thành Điểm trung bình tối thiểu."""
    if "Minavgmarktopass" in text:
        text = text.replace("Minavgmarktopass", "Điểm trung bình tối thiểu")

    """Sửa Isactive thành Hoạt động."""
    if "Isactive" in text:
        text = text.replace("Isactive", "Hoạt động")

    """Sửa StudentTasks thành Nhiệm vụ sinh viên."""
    if "StudentTasks" in text:
        text = text.replace("StudentTasks", "Nhiệm vụ sinh viên")

    return text

# Trích xuất văn bản
def extract_table_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    if not table:
        return "Không tìm thấy bảng trong syllabus."
    
    result_lines = []
    
    """ Duyệt qua từng hàng trong bảng và lấy nội dung văn bản """
    rows = table.find_all("tr")
    for row in rows:
        cols = row.find_all(["td", "th"])
        if len(cols) >= 2:
            attr = clean(cols[0].get_text())
            val = clean(cols[1].get_text())

            # Dịch nội dung nếu cần
            attr_vi = translate_text(attr)
            val_vi = translate_text(val)

            # Sửa đổi văn bản nếu cần
            attr_vi = modify_table_text(attr_vi)
            val_vi = modify_table_text(val_vi)

            # Thêm vào kết quả
            result_lines.append(f"{attr_vi}: {val_vi}")
        
        elif len(cols) == 1:
            # Nếu chỉ có một cột, dịch và thêm vào kết quả
            content = clean(cols[0].get_text())
            content_vi = translate_text(content)

            # Sửa đổi văn bản nếu cần
            content_vi = modify_table_text(content_vi)
            result_lines.append(content_vi)

    return "\n".join(result_lines)        

# Lấy nội dung syllabus từ web
def process_urls(urls):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state=SESSION_FILE)
        page = context.new_page()

        for idx, url in enumerate(urls):
            try:
                """Truy cập từng URL trong danh sách và lấy nội dung"""
                print(f"🔍 Đang xử lý URL {idx + 1}/{len(urls)}: {url}")
                page.goto(url)
                page.wait_for_load_state("networkidle")
                page.wait_for_timeout(2000)

                html = page.content()
                text = extract_table_text(html)
                print(f"✅ Đã lấy nội dung từ {url}")
                with open(f"syllabus_{idx + 1}.html", "w", encoding="utf-8") as f:
                    f.write(text)

                """ In nội dung đã dịch """
                # print(f"📄 Nội dung đã dịch từ {url}:\n{text}\n")

                # Lưu embedding vào Qdrant
                create_and_store_embedding(text, url)

                # Xóa file HTML sau khi đã lưu embedding
                os.remove(f"syllabus_{idx + 1}.html")

            except Exception as e:
                print(f"❌ Lỗi khi xử lý {url}: {e}")

        browser.close()
                

if __name__ == "__main__":
    urls = [
        "https://flm.fpt.edu.vn/gui/role/student/SyllabusDetails?sylid=11212",
        "https://flm.fpt.edu.vn/gui/role/student/SyllabusDetails?sylid=11246",
        "https://flm.fpt.edu.vn/gui/role/student/SyllabusDetails?sylid=11853",
        "https://flm.fpt.edu.vn/gui/role/student/SyllabusDetails?sylid=12224",
        "https://flm.fpt.edu.vn/gui/role/student/SyllabusDetails?sylid=12594",
        "https://flm.fpt.edu.vn/gui/role/student/SyllabusDetails?sylid=10473",
        "https://flm.fpt.edu.vn/gui/role/student/SyllabusDetails?sylid=11098",
        "https://flm.fpt.edu.vn/gui/role/student/SyllabusDetails?sylid=10369",
        "https://flm.fpt.edu.vn/gui/role/student/SyllabusDetails?sylid=12039",
        "https://flm.fpt.edu.vn/gui/role/student/SyllabusDetails?sylid=11845",
        "https://flm.fpt.edu.vn/gui/role/student/SyllabusDetails?sylid=11214",
        "https://flm.fpt.edu.vn/gui/role/student/SyllabusDetails?sylid=12627",
        "https://flm.fpt.edu.vn/gui/role/student/SyllabusDetails?sylid=12746",
        "https://flm.fpt.edu.vn/gui/role/student/SyllabusDetails?sylid=11252",
        "https://flm.fpt.edu.vn/gui/role/student/SyllabusDetails?sylid=10422",
        "https://flm.fpt.edu.vn/gui/role/student/SyllabusDetails?sylid=10736",
        "https://flm.fpt.edu.vn/gui/role/student/SyllabusDetails?sylid=8972",
        "https://flm.fpt.edu.vn/gui/role/student/SyllabusDetails?sylid=12079",
        "https://flm.fpt.edu.vn/gui/role/student/SyllabusDetails?sylid=12745",
        "https://flm.fpt.edu.vn/gui/role/student/SyllabusDetails?sylid=12557",
        "https://flm.fpt.edu.vn/gui/role/student/SyllabusDetails?sylid=12092",
        "https://flm.fpt.edu.vn/gui/role/student/SyllabusDetails?sylid=12631",
        "https://flm.fpt.edu.vn/gui/role/student/SyllabusDetails?sylid=12549",
        "https://flm.fpt.edu.vn/gui/role/student/SyllabusDetails?sylid=12281",
        "https://flm.fpt.edu.vn/gui/role/student/SyllabusDetails?sylid=12547",
        "https://flm.fpt.edu.vn/gui/role/student/SyllabusDetails?sylid=10358",
        "https://flm.fpt.edu.vn/gui/role/student/SyllabusDetails?sylid=12548",
        "https://flm.fpt.edu.vn/gui/role/student/SyllabusDetails?sylID=11218",
        "https://flm.fpt.edu.vn/gui/role/student/SyllabusDetails?sylID=12550",
        "https://flm.fpt.edu.vn/gui/role/student/SyllabusDetails?sylID=11217"
    ]

    process_urls(urls)

    result, _ = qdrant_client.scroll(
        collection_name=collection_name,
        with_payload=True,
        with_vectors=True,  # Không cần vector nếu chỉ muốn xem nội dung
        limit=30
    )

    data = []
    for point in result:
        data.append({
            "ID": point.id,
            "URL": point.payload.get("url", ""),
             "Văn bản": point.payload.get("văn bản", "")
        })

    df = pd.DataFrame(data)
    print(df.to_string(index=False))
    # Lưu DataFrame vào file CSV
    df.to_csv("DataCollection\syllabus_data.csv", index=False, encoding="utf-8-sig")
    print("✅ Dữ liệu đã được lưu vào 'syllabus_data.csv'")