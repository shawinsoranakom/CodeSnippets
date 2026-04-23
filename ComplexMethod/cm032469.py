def wait_for_dataset_detail_ready(page, expect, timeout_ms: int) -> None:
    """Wait for dataset detail UI to become ready/visible."""
    wait_for_dataset_detail(page, timeout_ms=timeout_ms)
    try:
        page.wait_for_load_state("networkidle", timeout=timeout_ms)
    except Exception:
        try:
            page.wait_for_load_state("domcontentloaded", timeout=timeout_ms)
        except Exception:
            pass

    heading = page.locator("[role='heading']").first
    main = page.locator("[role='main']").first
    if main.count() > 0:
        anchor = main.locator("text=/\\b(add|upload|file|document)\\b/i").first
    else:
        anchor = page.locator("text=/\\b(add|upload|file|document)\\b/i").first
    try:
        if heading.count() > 0:
            expect(heading).to_be_visible(timeout=timeout_ms)
            return
        if main.count() > 0:
            expect(main).to_be_visible(timeout=timeout_ms)
            return
        expect(anchor).to_be_visible(timeout=timeout_ms)
    except AssertionError:
        if env_bool("PW_DEBUG_DUMP"):
            url = page.url
            button_count = page.locator("button, [role='button']").count()
            body_text = page.evaluate(
                "(() => (document.body && document.body.innerText) || '')()"
            )
            debug(
                f"[dataset] detail_ready_failed url={url} button_count={button_count}"
            )
            debug(f"[dataset] body_text_snippet={body_text[:200]!r}")
        raise