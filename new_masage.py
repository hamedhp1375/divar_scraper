import time
from hmac import new
from wsgiref.validate import validator

from playwright.sync_api import sync_playwright
from fastapi import FastAPI

app = FastAPI()

PROFILE_PATH = "divar_profile"
urls = []
#
# def login_divar(page, number):
#     page.goto("https://divar.ir/chat", wait_until="domcontentloaded")
#     page.wait_for_timeout(3000)
#
#     login_button = page.locator("button:has-text('ورود به حساب کاربری')")
#
#     if login_button.count() > 0:
#         print("در حال لاگین...")
#
#         login_button.first.click()
#
#         page.wait_for_selector('input[name="mobile"]')
#         page.fill('input[name="mobile"]', number)
#
#         page.click('button.auth-actions__submit-button')
#
#         page.wait_for_selector('input[name="code"]', timeout=15000)
#         otp = input("کد پیامک را وارد کنید: ")
#         page.fill('input[name="code"]', otp)
#         page.keyboard.press("Enter")
#
#         page.wait_for_timeout(3000)
#         print("لاگین انجام شد ✅")
#     else:
#         print("قبلاً لاگین شده‌ای ✅")


def click_unread_filter(page):
    """کلیک روی چیپ خوانده‌نشده"""
    page.wait_for_timeout(2000)

    unread_chip = page.locator("span.kt-chip:has-text('خوانده‌نشده')")

    if unread_chip.count() > 0:
        unread_chip.first.click()
        print("فیلتر خوانده‌نشده فعال شد ✅")

        # صبر برای رندر مجدد لیست
        page.wait_for_timeout(2000)
    else:
        print("چیپ خوانده‌نشده پیدا نشد ❌")


def open_all_chats_and_get_urls(page):
    """باز کردن همه چت‌ها و گرفتن URL آنها"""

    page.wait_for_timeout(2000)

    # بررسی empty state
    empty_state = page.locator(
        "div.kt-empty-state__description:has-text('پیامی وجود ندارد')"
    )
    if empty_state.count() == 1:
        print("ییام جدیدی وجود ندارد")
        return []
    else:
        chat_links = page.locator("a[href^='/chat/']")


        # حلقه روی همه چت‌ها
        count = chat_links.count()
        print(f"{count} چت پیدا شد 🔥")

        for i in range(count):
            chat_links.nth(i).click()
            page.wait_for_load_state("networkidle")  # صبر برای لود کامل چت

            current_url = page.url
            print("URL:", current_url)
            urls.append(current_url)
            time.sleep(1)
            page.go_back()  # برگشت به لیست چت‌ها
            page.wait_for_load_state("networkidle")
            time.sleep(2)

        return urls




def main():
    number = input("شماره خود را وارد کنید (مثال: 09171234567): ").strip()

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=PROFILE_PATH,
            headless=False
        )

        page = context.new_page()
        time.sleep(5)
        # login_divar(page, number)
        # time.sleep(5)
        # 👇 اول فیلتر
        # click_unread_filter(page)
        # time.sleep(5)
        # 👇 بعد باز کردن چت
        open_all_chats_and_get_urls(page)
        print(urls)

        page.wait_for_timeout(200000)


if __name__ == "__main__":
    main()