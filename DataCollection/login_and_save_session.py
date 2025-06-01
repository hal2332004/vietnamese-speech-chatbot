from playwright.sync_api import sync_playwright
import json

SESSION_FILE = "E:\CN AI\SU2025\DAT301m\DataCollection\session.json"
LOGIN_URL = "https://flm.fpt.edu.vn/DefaultSignin"

def save_storage(context):
    context.storage_state(path=SESSION_FILE)
    print(f"✅ Session saved to {SESSION_FILE}")

def login_and_save_session():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=50)
        context = browser.new_context()
        page = context.new_page()

        page.goto(LOGIN_URL)
        page.wait_for_load_state("networkidle")
        print("👉 Vui lòng chọn Education Level và đăng nhập bằng Google thủ công.")

        input("⏳ Sau khi hoàn tất đăng nhập, nhấn ENTER để tiếp tục...")

        save_storage(context)
        browser.close()

if __name__ == "__main__":
    login_and_save_session()