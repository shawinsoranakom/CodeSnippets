def _wait_for_catchphrase(page: Page, timeout_s: int = 300) -> None:
    start = time.time()
    pattern = re.compile('|'.join(CATCHPHRASE_PATTERNS), re.IGNORECASE)

    while time.time() - start < timeout_s:
        try:
            messages = page.locator('[data-testid="agent-message"]').all()
            for i, msg in enumerate(messages):
                try:
                    content = msg.text_content() or ''
                    if pattern.search(content):
                        _screenshot(page, f'catchphrase_found_{i}')
                        return
                except Exception:
                    continue
        except Exception:
            pass

        # also search globally on page for the phrase in case rendering differs
        try:
            if page.get_by_text('Code Less, Make More', exact=False).is_visible(
                timeout=1000
            ):
                _screenshot(page, 'catchphrase_found_global')
                return
        except Exception:
            pass

        page.wait_for_timeout(2000)

    raise AssertionError(
        'Agent did not return the expected catchphrase within time limit'
    )