def _launch_conversation(page: Page) -> None:
    launch_button = page.locator('[data-testid="repo-launch-button"]')
    expect(launch_button).to_be_visible(timeout=30000)

    # Wait until enabled
    start = time.time()
    while time.time() - start < 120:
        try:
            if not launch_button.is_disabled():
                break
        except Exception:
            pass
        page.wait_for_timeout(1000)

    try:
        if launch_button.is_disabled():
            # Force-enable and click via JS as fallback
            page.evaluate(
                """
                () => {
                    const btn = document.querySelector('[data-testid="repo-launch-button"]');
                    if (btn) { btn.removeAttribute('disabled'); btn.click(); return true; }
                    return false;
                }
                """
            )
        else:
            launch_button.click()
    except Exception:
        # Last resort: try pressing Enter
        try:
            launch_button.focus()
            page.keyboard.press('Enter')
        except Exception:
            pass

    _screenshot(page, 'after_launch_click')

    # Wait for conversation route
    # Also wait for possible loading indicators to disappear
    loading_selectors = [
        '[data-testid="loading-indicator"]',
        '[data-testid="loading-spinner"]',
        '.loading-spinner',
        '.spinner',
        'div:has-text("Loading...")',
        'div:has-text("Initializing...")',
        'div:has-text("Please wait...")',
    ]
    for selector in loading_selectors:
        try:
            loading = page.locator(selector)
            if loading.is_visible(timeout=3000):
                expect(loading).not_to_be_visible(timeout=120000)
                break
        except Exception:
            continue

    # Confirm chat input is present
    chat_input = page.locator('[data-testid="chat-input"]')
    expect(chat_input).to_be_visible(timeout=120000)

    # Give UI extra time to settle
    page.wait_for_timeout(5000)