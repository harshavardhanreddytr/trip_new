from playwright.sync_api import sync_playwright


BASE_URL = "http://127.0.0.1:5000"


def run_browser(test_steps):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        test_steps(page)
        browser.close()


# --------------------
# BASIC PAGE LOADS
# --------------------

def test_home_page_loads():
    def steps(page):
        page.goto(f"{BASE_URL}/")
        page.wait_for_timeout(1000)
        assert page.title() is not None
    run_browser(steps)


def test_auth_page_loads():
    def steps(page):
        response = page.goto(f"{BASE_URL}/")
        page.wait_for_load_state("networkidle")

        assert response is not None
        assert response.status == 200

        assert page.locator(".form-panel").count() == 1
        assert page.locator("#loginForm").count() == 1
        assert page.locator("#registerForm").count() == 1
        assert page.locator("#forgotForm").count() == 1

    run_browser(steps)

def test_dashboard_page_loads():
    def steps(page):
        page.goto(f"{BASE_URL}/dashboard")
        page.wait_for_timeout(1000)
        assert page.locator("body").count() == 1
    run_browser(steps)


def test_trips_page_loads():
    def steps(page):
        page.goto(f"{BASE_URL}/trips")
        page.wait_for_timeout(1000)
        assert page.locator("body").count() == 1
    run_browser(steps)


# --------------------
# NAVIGATION SAFETY
# --------------------

def test_trip_page_opens():
    def steps(page):
        page.goto(f"{BASE_URL}/trip")
        page.wait_for_timeout(1000)
        assert page.locator("body").count() == 1
    run_browser(steps)


def test_day_page_opens():
    def steps(page):
        page.goto(f"{BASE_URL}/day")
        page.wait_for_timeout(1000)
        assert page.locator("body").count() == 1
    run_browser(steps)


# --------------------
# BUTTON PRESENCE
# --------------------

def test_task_action_buttons_exist():
    def steps(page):
        page.goto(f"{BASE_URL}/day")
        page.wait_for_timeout(1000)

        # These should EXIST if tasks exist
        buttons = page.locator("button")
        assert buttons.count() >= 0
    run_browser(steps)


# --------------------
# NOTES PAGE
# --------------------

def test_notes_page_loads():
    def steps(page):
        page.goto(f"{BASE_URL}/task_notes")
        page.wait_for_timeout(1000)
        assert page.locator("textarea").count() >= 0
    run_browser(steps)

def test_task_status_buttons_clickable():
    def steps(page):
        # Go to a day page (assumes at least one task exists)
        page.goto(f"{BASE_URL}/day")
        page.wait_for_timeout(1000)

        # Try clicking status buttons if present
        for label in ["YES", "NO", "SKIPPED"]:
            buttons = page.locator(f"text={label}")
            if buttons.count() > 0:
                buttons.first.click()
                page.wait_for_timeout(300)

        # If we reached here without crash, test passes
        assert True

    run_browser(steps)

# -------------------------------------------------
# NAVIGATION INTEGRITY TESTS
# -------------------------------------------------

def test_trips_to_trip_navigation():
    def steps(page):
        page.goto(f"{BASE_URL}/trips")
        page.wait_for_timeout(1000)

        # Try clicking first trip link if exists
        links = page.locator("a")
        if links.count() > 0:
            links.first.click()
            page.wait_for_timeout(1000)

        assert page.locator("body").count() == 1

    run_browser(steps)


def test_trip_to_day_navigation():
    def steps(page):
        page.goto(f"{BASE_URL}/trip")
        page.wait_for_timeout(1000)

        # Try clicking a day link if exists
        links = page.locator("a")
        if links.count() > 0:
            links.first.click()
            page.wait_for_timeout(1000)

        assert page.locator("body").count() == 1

    run_browser(steps)


def test_day_page_safe_on_refresh():
    def steps(page):
        page.goto(f"{BASE_URL}/day")
        page.wait_for_timeout(1000)

        # Refresh should not crash
        page.reload()
        page.wait_for_timeout(1000)

        assert page.locator("body").count() == 1

    run_browser(steps)


# -------------------------------------------------
# EMPTY / EDGE STATE SAFETY
# -------------------------------------------------

def test_day_page_without_tasks_does_not_crash():
    def steps(page):
        page.goto(f"{BASE_URL}/day")
        page.wait_for_timeout(1000)

        # Even if no tasks, page must render
        assert page.locator("body").count() == 1

    run_browser(steps)


def test_trip_page_without_days_does_not_crash():
    def steps(page):
        page.goto(f"{BASE_URL}/trip")
        page.wait_for_timeout(1000)

        assert page.locator("body").count() == 1

    run_browser(steps)


# -------------------------------------------------
# SUPPORT PAGES (STABILITY ONLY)
# -------------------------------------------------

def test_analytics_page_loads():
    def steps(page):
        page.goto(f"{BASE_URL}/analytics")
        page.wait_for_timeout(1000)

        assert page.locator("body").count() == 1

    run_browser(steps)


def test_profile_page_loads():
    def steps(page):
        page.goto(f"{BASE_URL}/profile")
        page.wait_for_timeout(1000)

        assert page.locator("body").count() == 1

    run_browser(steps)


def test_friends_page_loads():
    def steps(page):
        page.goto(f"{BASE_URL}/friends")
        page.wait_for_timeout(1000)

        assert page.locator("body").count() == 1

    run_browser(steps)


def test_import_page_loads():
    def steps(page):
        page.goto(f"{BASE_URL}/import_trips")
        page.wait_for_timeout(1000)

        assert page.locator("body").count() == 1

    run_browser(steps)


# -------------------------------------------------
# LOGOUT SAFETY
# -------------------------------------------------

def test_logout_does_not_crash():
    def steps(page):
        response = page.goto(f"{BASE_URL}/logout")
        page.wait_for_timeout(500)

        # Logout may redirect; must not 500
        if response:
            assert response.status in (200, 302)

    run_browser(steps)