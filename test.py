from fastapi import FastAPI
from contextlib import asynccontextmanager
from playwright.async_api import async_playwright
from pydantic import BaseModel

PROFILE_PATH = "divar_profile"


class PhoneRequest(BaseModel):
    number: str


class OTPRequest(BaseModel):
    otp: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    # -------- Startup --------
    playwright = await async_playwright().start()
    browser_context = await playwright.chromium.launch_persistent_context(
        user_data_dir=PROFILE_PATH,
        headless=False
    )

    app.state.playwright = playwright
    app.state.browser_context = browser_context

    yield

    # -------- Shutdown --------
    await browser_context.close()
    await playwright.stop()


app = FastAPI(lifespan=lifespan)


@app.post("/send-otp")
async def send_otp(data: PhoneRequest):
    context = app.state.browser_context
    page = await context.new_page()

    try:
        await page.goto("https://divar.ir/chat")

        login_button = page.locator("button:has-text('ورود به حساب کاربری')")

        if await login_button.count() > 0:
            await login_button.first.click()
            await page.wait_for_selector('input[name="mobile"]')
            await page.fill('input[name="mobile"]', data.number)
            await page.click('button.auth-actions__submit-button')
            return {"message": "OTP ارسال شد ✅"}

        return {"message": "قبلاً لاگین شده‌ای ✅"}

    except Exception as e:
        return {"error": str(e)}

    finally:
        await page.close()


@app.post("/verify-otp")
async def verify_otp(data: OTPRequest):
    context = app.state.browser_context
    page = await context.new_page()

    try:
        await page.goto("https://divar.ir/chat")

        await page.wait_for_selector('input[name="code"]')
        await page.fill('input[name="code"]', data.otp)
        await page.keyboard.press("Enter")
        await page.wait_for_timeout(3000)

        return {"message": "لاگین با موفقیت انجام شد ✅"}

    except Exception as e:
        return {"error": str(e)}

    finally:
        await page.close()