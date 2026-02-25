from fastapi import FastAPI
from playwright.sync_api import sync_playwright
import time

from login import playwright_context

app = FastAPI()

PROFILE_PATH = "divar_profile"


def click_unread_filter(page):
    """کلیک روی چیپ خوانده‌نشده"""
    page.wait_for_timeout(2000)
    unread_chip = page.locator("span.kt-chip:has-text('خوانده‌نشده')")
    if unread_chip.count() > 0:
        unread_chip.first.click()
        page.wait_for_timeout(2000)


def open_all_chats_and_get_urls(page):
    """باز کردن همه چت‌ها و گرفتن URLها"""
    urls = []
    page.wait_for_timeout(2000)

    empty_state = page.locator(
        "div.kt-empty-state__description:has-text('پیامی وجود ندارد')"
    )
    if empty_state.count() == 1:
        return urls

    chat_links = page.locator("a[href^='/chat/']")
    count = chat_links.count()

    for i in range(count):
        chat_links.nth(i).click()
        page.wait_for_load_state("networkidle")
        urls.append(page.url)
        time.sleep(1)
        page.go_back()
        page.wait_for_load_state("networkidle")
        time.sleep(1)

    return urls


@app.get("/get-urls")
def get_urls():
    """گرفتن URLهای چت‌ها بدون لاگین"""
    try:
        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                user_data_dir=PROFILE_PATH,
                headless=False  # True اگر نمیخوای مرورگر باز باشه
            )
            page = context.new_page()
            page.goto("https://divar.ir/chat")
            time.sleep(3)

            # 👇 فیلتر خوانده نشده (اختیاری)
            click_unread_filter(page)

            # گرفتن URLها
            urls = open_all_chats_and_get_urls(page)

            # بستن صفحه و context
            page.close()
            context.close()

            return {"urls": urls}

    except Exception as e:
        return {"error": str(e)}
    # uvicorn unread_massage:app --reload
    # جهت تست
    # http://127.0.0.1:8000/get-urls