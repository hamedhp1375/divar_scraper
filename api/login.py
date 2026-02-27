from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from playwright.sync_api import sync_playwright

app = FastAPI()

PROFILE_PATH = "divar_profile"

playwright_instance = None
playwright_context = None
page = None


class AuthRequest(BaseModel):
    number: Optional[str] = None
    otp: Optional[str] = None


@app.post("/auth")
def auth(data: AuthRequest):
    global playwright_instance, playwright_context, page

    # 🔥 اگر هنوز Playwright روشن نشده باشه
    if playwright_instance is None:
        playwright_instance = sync_playwright().start()

        playwright_context = playwright_instance.chromium.launch_persistent_context(
            user_data_dir=PROFILE_PATH,
            headless=False
        )

        page = playwright_context.new_page()
        page.goto("https://divar.ir/chat")

        print("Playwright Started ✅")

    # 🔹 اگر شماره ارسال شد
    if data.number:
        login_button = page.locator("button:has-text('ورود به حساب کاربری')")

        if login_button.count() > 0:
            login_button.first.click()
            page.wait_for_selector('input[name="mobile"]')
            page.fill('input[name="mobile"]', data.number)
            page.click('button.auth-actions__submit-button')
            return {"message": "OTP ارسال شد ✅"}

        else:
            if page:
                page.close()
                page = None

            if playwright_context:
                playwright_context.close()
                playwright_context = None

            if playwright_instance:
                playwright_instance.stop()
                playwright_instance = None
            return {"message": "قبلاً لاگین شده‌ای ✅"}

    # 🔹 اگر OTP ارسال شد
    elif data.otp:
        page.wait_for_selector('input[name="code"]')
        page.fill('input[name="code"]', data.otp)
        page.keyboard.press("Enter")
        page.wait_for_timeout(3000)
        if page:
            page.close()
            page = None

        if playwright_context:
            playwright_context.close()
            playwright_context = None

        if playwright_instance:
            playwright_instance.stop()
            playwright_instance = None
        return {"message": "لاگین موفق ✅"}

    else:
        raise HTTPException(status_code=400, detail="number یا otp ارسال کن")