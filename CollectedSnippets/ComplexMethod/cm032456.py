def _mm_click_generic_model_option(page, card_index: int, option_prefix: str) -> str:
    popover_root = page.locator("[data-radix-popper-content-wrapper]").last
    options = popover_root.locator("[role='option']")
    expect(options.first).to_be_visible(timeout=RESULT_TIMEOUT_MS)

    option_count = options.count()
    choose_index = 1 if option_count > 1 and card_index == 1 else 0
    chosen = options.nth(choose_index)
    chosen.scroll_into_view_if_needed()

    for _ in range(3):
        try:
            chosen.click(timeout=2000, force=True)
            break
        except Exception:
            page.wait_for_timeout(120)
    else:
        raise AssertionError("failed to click fallback generic model option")

    chosen_testid = chosen.get_attribute("data-testid") or ""
    if chosen_testid:
        return chosen_testid

    chosen_value = (
        chosen.get_attribute("data-value")
        or chosen.get_attribute("value")
        or f"idx-{choose_index}"
    )
    return f"{option_prefix}{chosen_value}"