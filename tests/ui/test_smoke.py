from playwright.sync_api import sync_playwright


def test_home_page_loads():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto("http://127.0.0.1:5000/")
        page.wait_for_timeout(1000)

        assert page.title() is not None

        browser.close()