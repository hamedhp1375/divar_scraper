from fastapi import FastAPI
from pydantic import BaseModel
from playwright.sync_api import sync_playwright
import time

app = FastAPI()

PROFILE_PATH = "divar_profile"

class RequestData(BaseModel):
    category: str


@app.post("/run")
def run_script(data: RequestData):

    category = str(data.category)

    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=PROFILE_PATH,
            headless=False
        )

        # اگر page قبلی وجود داشت همون رو بگیر
        page = browser.pages[0] if browser.pages else browser.new_page()

        # 1️⃣ ورود به دیوار شیراز
        page.goto("https://divar.ir/s/shiraz")
        page.wait_for_selector('input[name="search"]')

        # 2️⃣ جستجو
        page.fill('input[name="search"]', category)
        page.keyboard.press("Enter")

        # 3️⃣ صبر تا کارت‌ها
        page.wait_for_selector("a.kt-post-card__action", timeout=15000)

        # 4️⃣ گرفتن 20 لینک اول
        links = page.eval_on_selector_all(
            "a.kt-post-card__action",
            "els => els.slice(0, 20).map(e => e.href)"
        )

        print(f"{len(links)} آگهی پیدا شد")

        for i, link in enumerate(links, start=1):
            print(f"\n({i}) باز کردن:", link)
            page.goto(link)
            page.wait_for_load_state("networkidle")

            # ================== گرفتن قیمت ==================
            try:
                price_el = page.locator(
                    'div.kt-unexpandable-row:has(p.kt-unexpandable-row__title:text("قیمت")) '
                    'p.kt-unexpandable-row__value'
                )
                price_el.wait_for(timeout=5000)
                price = price_el.inner_text()
            except:
                price = "نامشخص"

            print("قیمت:", price)

            # ================== اطلاعات تماس ==================
            page.wait_for_selector("button.post-actions__get-contact", timeout=15000)
            page.click("button.post-actions__get-contact")

            # ================== گرفتن شماره تماس ==================
            try:
                phone_el = page.locator('a[href^="tel:"]')
                phone_el.wait_for(timeout=15000)
                phone = phone_el.get_attribute("href").replace("tel:", "")
            except:
                phone = "ندارد"

            print("شماره:", phone)

            # ================== ذخیره ==================
            with open("../results.txt", "a", encoding="utf-8") as f:
                f.write(f"{phone} | {price}\n")

            time.sleep(5)
            page.go_back()
            page.wait_for_selector("a.kt-post-card__action")

        browser.close()

    return {"status": "done"}