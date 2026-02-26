from fileinput import close

from fastapi import FastAPI
from pydantic import BaseModel
from playwright.sync_api import sync_playwright
import time

app = FastAPI()

PROFILE_PATH = "divar_profile"

# نگه داشتن context و page بین درخواست‌ها
playwright_context = None
page = None

# مدل برای دریافت شماره
class PhoneRequest(BaseModel):
    number: str

# مدل برای OTP
class OTPRequest(BaseModel):
    otp: str


@app.post("/send-otp")
def send_otp(data: PhoneRequest):
    global playwright_context, page
    p = sync_playwright().start()
    playwright_context = p.chromium.launch_persistent_context(
        user_data_dir=PROFILE_PATH,
        headless=False
    )

    page = playwright_context.new_page()
    page.goto("https://divar.ir/chat")

    login_button = page.locator("button:has-text('ورود به حساب کاربری')")

    try:
        if login_button.count() > 0:
            login_button.first.click()
            page.wait_for_selector('input[name="mobile"]')
            page.fill('input[name="mobile"]', data.number)
            page.click('button.auth-actions__submit-button')
            message = "OTP ارسال شد ✅"
        else:
            page.close()
            playwright_context.close()
            page = None
            playwright_context = None
            message = "قبلاً لاگین شده‌ای ✅"

        # 👇 بستن صفحه و context در هر صورت
            p.stop()

        return {"message": message}

    except Exception as e:
        # اگر خطایی رخ داد، page و context بسته بشن
        if page:
            page.close()
        if playwright_context:
            playwright_context.close()
        page = None
        playwright_context = None
        return {"error": str(e)}



@app.post("/verify-otp")
def verify_otp(data: OTPRequest):
    global page, playwright_context

    if page is None:
        return {"error": "ابتدا /send-otp را صدا بزنید!"}

    try:
        # پر کردن OTP و ورود
        page.wait_for_selector('input[name="code"]')
        page.fill('input[name="code"]', data.otp)
        page.keyboard.press("Enter")
        page.wait_for_timeout(3000)

        # بستن صفحه و context
        page.close()
        playwright_context.close()

        # پاک کردن referenceها
        page = None
        playwright_context = None

        return {"message": "لاگین با موفقیت انجام شد و صفحه بسته شد ✅"}

    except Exception as e:
        return {"error": str(e)}

 # uvicorn test2:app --reload
#  جهت تست
# http://127.0.0.1:8000/send-otp
# {
#   "number": "951549"
# }
# http://127.0.0.1:8000/verify-otp
# {
# "otp":"1234"
