from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from playwright.sync_api import sync_playwright
import time

app = FastAPI()

PROFILE_PATH = "divar_profile"

scheduler = BackgroundScheduler()
# برای راهندازی وب هوک
# نیاز به وب سرویس دارد برای فرستادن پاسخ
#
# def call_get_urls():
#     try:
#         response = requests.get("http://127.0.0.1:8000/get-urls")
#         print("Hook Sent ✅", response.status_code)
#     except Exception as e:
#         print("Error ❌", e)
#     urls = get_urls()
#     # ارسال به وب‌هوک
#     requests.post("https://example.com/hook", json=urls)
#
#
# # اضافه کردن job هر 5 دقیقه
# scheduler.add_job(
#     call_get_urls,
#     "interval",
#     minutes=1,
#     max_instances=1,  # فقط یک اجرا همزمان
#     coalesce=True  # اگر یکی جا افتاد، یکی اجرا کن
# )
#
#
# @app.on_event("startup")
# def start_scheduler():
#     scheduler.start()
#     print("Scheduler started 🚀")
#
#
# @app.on_event("shutdown")
# def shutdown_scheduler():
#     scheduler.shutdown()


def click_unread_filter(page):
    """کلیک روی چیپ خوانده‌نشده"""
    page.wait_for_timeout(5000)
    unread_chip = page.locator("span.kt-chip:has-text('خوانده‌نشده')")
    if unread_chip.count() > 0:
        unread_chip.first.click()
        page.wait_for_timeout(5000)


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
            time.sleep(3)
            # گرفتن URLها
            urls = open_all_chats_and_get_urls(page)

            # بستن صفحه و context
            page.close()
            context.close()

            return {"urls": urls}

    except Exception as e:
        return {"error": str(e)}
# برای استپ کردن وب هوک

# @app.post("/stop-scheduler")
# def stop_scheduler():
#     scheduler.shutdown()
#     return {"message": "Scheduler stopped ✅"}


# uvicorn unread_massage:app --reload
# جهت تست
# http://127.0.0.1:8000/get-urls

# جهت تست وب هوک
# uvicorn unread_massage:app