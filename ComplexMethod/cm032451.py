def select_ragflow_option(
    page,
    trigger_test_id: str,
    preferred_text: str | None = None,
) -> str:
    trigger = page.get_by_test_id(trigger_test_id).first
    expect(trigger).to_be_visible(timeout=RESULT_TIMEOUT_MS)
    trigger.scroll_into_view_if_needed()
    current_text = ""
    try:
        current_text = trigger.inner_text().strip()
    except Exception:
        current_text = ""
    trigger.click()

    options = page.locator("[role='option']")
    expect(options.first).to_be_visible(timeout=RESULT_TIMEOUT_MS)

    if preferred_text:
        preferred_option = options.filter(
            has_text=re.compile(rf"^{re.escape(preferred_text)}$", re.I)
        )
        if preferred_option.count() > 0:
            preferred_option.first.click()
            return preferred_text

    selected_text = ""
    option_count = options.count()
    for idx in range(option_count):
        option = options.nth(idx)
        try:
            if not option.is_visible():
                continue
        except Exception:
            continue
        text = option.inner_text().strip()
        if not text:
            continue
        if current_text and text.lower() == current_text.lower() and option_count > 1:
            continue
        option.click()
        selected_text = text
        break

    if not selected_text:
        fallback = options.first
        selected_text = fallback.inner_text().strip()
        fallback.click()
    return selected_text