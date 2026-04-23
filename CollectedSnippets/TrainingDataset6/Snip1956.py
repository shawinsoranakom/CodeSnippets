def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    # Update the viewport manually
    context = browser.new_context(viewport={"width": 960, "height": 1080})
    page = context.new_page()
    page.goto("http://localhost:8000/docs")
    page.get_by_label("post /heroes/").click()
    # Manually add the screenshot
    page.screenshot(path="docs/en/docs/img/tutorial/sql-databases/image01.png")

    # ---------------------
    context.close()
    browser.close()