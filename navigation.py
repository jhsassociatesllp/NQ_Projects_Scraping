from playwright.sync_api import sync_playwright

LOGIN_URL = "https://nexusquant.in/PMS/"

EMAIL = "huzeifa.unwala@jhsassociates.in"
PASSWORD = "Pass@123"

def run_bot():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,  # keep False for debugging
            slow_mo=50       # helps with flaky UI
        )

        context = browser.new_context()
        page = context.new_page()

        # ================= LOGIN =================
        page.goto(LOGIN_URL, timeout=60000)

        page.fill("input#email", EMAIL)
        page.fill("input#password", PASSWORD)

        page.click("button[type='submit']")

        # Wait for home page (adjust if URL differs)
        page.wait_for_load_state("networkidle")

        print("✅ Logged in")

        # ================= HOME → CONTROL PANEL =================
        page.wait_for_timeout(5000)  # explicit wait as requested

        page.click("#switch_to_control_panel")

        print("👉 Clicked Switch to Control Panel")

        # ================= POPUP CONFIRM =================
        page.wait_for_timeout(2000)

        # SweetAlert confirm button
        page.click("button.swal2-confirm")

        print("✅ Popup confirmed")

        # ================= PANEL LOAD =================
        page.wait_for_timeout(3000)

        # ================= PROJECTS MENU =================
        page.click("a[href='https://nexusquant.in/PMS/project-list']")

        print("📂 Projects clicked")

        # ================= WAIT FOR PROJECTS =================
        page.wait_for_timeout(8000)  # 5–10 seconds as requested

        print("✅ Projects loaded")

        # Keep browser open for inspection
        page.wait_for_timeout(5000)

        browser.close()


if __name__ == "__main__":
    run_bot()
