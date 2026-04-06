def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    # Update the viewport manually
    context = browser.new_context(viewport={"width": 960, "height": 1080})
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto("http://localhost:8000/docs")
    page.get_by_role("button", name="GET /items/ Read Items").click()
    page.get_by_role("button", name="Try it out").click()
    page.get_by_role("heading", name="Servers").click()
    # Manually add the screenshot
    page.screenshot(path="docs/en/docs/img/tutorial/query-param-models/image01.png")

    # ---------------------
    context.close()
    browser.close()