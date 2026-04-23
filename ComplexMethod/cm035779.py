def _send_prompt(page: Page, prompt: str) -> None:
    # Find input
    selectors = [
        '[data-testid="chat-input"] textarea',
        '[data-testid="message-input"]',
        'textarea',
        'form textarea',
    ]
    message_input = None
    for sel in selectors:
        try:
            el = page.locator(sel)
            if el.is_visible(timeout=5000):
                message_input = el
                break
        except Exception:
            continue

    if not message_input:
        raise AssertionError('Message input not found')

    message_input.fill(prompt)

    # Submit
    submit_selectors = [
        '[data-testid="chat-input"] button[type="submit"]',
        'button[type="submit"]',
        'button:has-text("Send")',
    ]
    submitted = False
    for sel in submit_selectors:
        try:
            btn = page.locator(sel)
            if btn.is_visible(timeout=3000):
                # wait until enabled
                start = time.time()
                while time.time() - start < 60:
                    try:
                        if not btn.is_disabled():
                            break
                    except Exception:
                        pass
                    page.wait_for_timeout(1000)
                try:
                    btn.click()
                    submitted = True
                    break
                except Exception:
                    pass
        except Exception:
            continue

    if not submitted:
        message_input.press('Enter')

    _screenshot(page, 'prompt_sent')