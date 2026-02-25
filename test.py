import time
from fastapi import FastAPI
from pydantic import BaseModel
from playwright.sync_api import sync_playwright

app = FastAPI()

PROFILE_PATH = "divar_profile"


# مدل داده‌ای برای دریافت شماره و OTP
class LoginRequest(BaseModel):
    number: str
    otp: str


urls = []


def login_divar(page, number, otp):
    page.goto("https://divar.ir/chat", wait_until="domcontentloaded")
    page.wait_for_timeout(3000)

    login_button = page.locator("button:has-text('ورود به حساب کاربری')")

    if login_button.count() > 0:
        login_button.first.click()
        page.wait_for_selector('input[name="mobile"]')
        page.fill('input[name="mobile"]', number)
        page.click('button.auth-actions__submit-button')
        page.wait_for_selector('input[name="code"]', timeout=15000)
        page.fill('input[name="code"]', otp)
        page.keyboard.press("Enter")
        page.wait_for_timeout(3000)
    else:
        print("قبلاً لاگین شده‌ای ✅")


def open_all_chats_and_get_urls(page):
    urls.clear()
    page.wait_for_timeout(2000)

    empty_state = page.locator(
        "div.kt-empty-state__description:has-text('پیامی وجود ندارد')"
    )
    if empty_state.count() == 1:
        print("پیام جدیدی وجود ندارد")
        return []
    else:
        chat_links = page.locator("a[href^='/chat/']")
        count = chat_links.count()
        print(f"{count} چت پیدا شد 🔥")

        for i in range(count):
            chat_links.nth(i).click()
            page.wait_for_load_state("networkidle")
            urls.append(page.url)
            time.sleep(1)
            page.go_back()
            page.wait_for_load_state("networkidle")
            time.sleep(2)

        return urls


@app.post("/get-urls")
def get_urls(data: LoginRequest):
    """API برای گرفتن URL چت‌ها"""
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=PROFILE_PATH,
            headless=False
        )
        page = context.new_page()
        time.sleep(5)
        login_divar(page, data.number, data.otp)
        time.sleep(5)
        open_all_chats_and_get_urls(page)
        return {"urls": urls}

    # uvicorn test:app --reload