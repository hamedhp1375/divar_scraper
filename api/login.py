from fastapi import FastAPI
from pydantic import BaseModel
from playwright.sync_api import sync_playwright

app = FastAPI()

PROFILE_PATH = "../divar_profile"

class PhoneRequest(BaseModel):
    number: str

class OTPRequest(BaseModel):
    otp: str

@app.post("/send-otp")
def send_otp(data: PhoneRequest):
    p = sync_playwright().start()
    context = None
    page = None
    try:
        # ساخت context و صفحه
        context = p.chromium.launch_persistent_context(
            user_data_dir=PROFILE_PATH,
            headless=False
        )
        page = context.new_page()
        page.goto("https://divar.ir/chat")

        login_button = page.locator("button:has-text('ورود به حساب کاربری')")

        if login_button.count() > 0:
            login_button.first.click()
            page.wait_for_selector('input[name="mobile"]')
            page.fill('input[name="mobile"]', data.number)
            page.click('button.auth-actions__submit-button')
            message = "OTP ارسال شد ✅"
        else:
            message = "قبلاً لاگین شده‌ای ✅"

        return {"message": message}

    except Exception as e:
        return {"error": str(e)}

    finally:
        # همیشه صفحه و context بسته شوند
        if page:
            page.close()
        if context:
            context.close()
        p.stop()


@app.post("/verify-otp")
def verify_otp(data: OTPRequest):
    p = sync_playwright().start()
    context = None
    page = None
    try:
        context = p.chromium.launch_persistent_context(
            user_data_dir=PROFILE_PATH,
            headless=False
        )
        page = context.new_page()
        page.goto("https://divar.ir/chat")

        # پر کردن OTP و ورود
        page.wait_for_selector('input[name="code"]')
        page.fill('input[name="code"]', data.otp)
        page.keyboard.press("Enter")
        page.wait_for_timeout(3000)

        return {"message": "لاگین با موفقیت انجام شد و صفحه بسته شد ✅"}

    except Exception as e:
        return {"error": str(e)}

    finally:
        if page:
            page.close()
        if context:
            context.close()
        p.stop()
 # uvicorn api.login:app --reload
#  جهت تست
# http://127.0.0.1:8000/send-otp
# {
#   "number": "951549"
# }
# http://127.0.0.1:8000/verify-otp
# {
# "otp":"1234"
# }
