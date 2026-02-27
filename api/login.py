from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from playwright.async_api import async_playwright
from pydantic import BaseModel
from typing import Optional

PROFILE_PATH = "divar_profile"

class AuthRequest(BaseModel):
    number: Optional[str] = None
    otp: Optional[str] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    # -------- Startup --------
    playwright = await async_playwright().start()
    browser_context = await playwright.chromium.launch_persistent_context(
        user_data_dir=PROFILE_PATH,
        headless=False
    )
    page = await browser_context.new_page()

    app.state.playwright = playwright
    app.state.browser_context = browser_context
    app.state.page = page

    yield

    # -------- Shutdown --------
    await page.close()
    await browser_context.close()
    await playwright.stop()


app = FastAPI(lifespan=lifespan)


@app.post("/auth")
async def auth(data: AuthRequest):
    page = app.state.page

    if data.number:
        await page.goto("https://divar.ir/chat")
        login_button = page.locator("button:has-text('ورود به حساب کاربری')")
        if await login_button.count() > 0:
            await login_button.first.click()
            await page.wait_for_selector('input[name="mobile"]')
            await page.fill('input[name="mobile"]', data.number)
            await page.click('button.auth-actions__submit-button')
            return {"message": "OTP ارسال شد ✅"}
        return {"message": "قبلاً لاگین شده‌ای ✅"}

    elif data.otp:
        try:
            code_input = page.locator('input[name="code"]')
            await code_input.wait_for(timeout=2000)
            await code_input.fill(data.otp)

            submit_button = page.locator('button.auth-actions__submit-button')
            if await submit_button.count() > 0:
                await submit_button.first.click()
            else:
                await page.keyboard.press("Enter")

            await page.wait_for_timeout(2000)
            return {"message": "لاگین موفق ✅"}
        except Exception:
            raise HTTPException(status_code=400, detail="صفحه کدتایید باز نشد لطفا ابتدا موبایل را وارد کنید همون روت ولی با موبایل")


    else:
        raise HTTPException(status_code=400, detail="number یا otp ارسال کن")
