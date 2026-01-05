from playwright.sync_api import sync_playwright

LOGIN_URL = "https://nexusquant.in/PMS/"

EMAIL = "huzeifa.unwala@jhsassociates.in"
PASSWORD = "Pass@123"

def login():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False  # keep False while developing
        )
        context = browser.new_context()
        page = context.new_page()

        # Open login page
        page.goto(LOGIN_URL, timeout=60000)

        # Fill email
        page.fill("input#email", EMAIL)

        # Fill password
        page.fill("input#password", PASSWORD)

        # Click Continue button
        page.click("button[type='submit']")

        # ⏳ WAIT FOR HOME PAGE
        # Option 1: wait for URL change
        page.wait_for_url("**/home**", timeout=60000)

        # Option 2 (safer): wait for a unique element on home page
        # page.wait_for_selector("text=Dashboard", timeout=60000)

        print("✅ Login successful")

        # Keep browser open for inspection
        page.wait_for_timeout(5000)

        browser.close()

if __name__ == "__main__":
    login()
