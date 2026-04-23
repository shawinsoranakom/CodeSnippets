def select_chunking_method_general(page, expect, modal, timeout_ms: int) -> None:
    """Select the General chunking method inside the dataset modal."""
    trigger_locator = modal.locator(
        "button",
        has=modal.locator(
            "span", has_text=re.compile(r"please select a chunking method\\.", re.I)
        ),
    ).first
    if trigger_locator.count() == 0:
        label = modal.locator("text=/please select a chunking method\\./i").first
        if label.count() > 0:
            trigger_locator = label.locator("xpath=ancestor::button[1]").first
        if trigger_locator.count() == 0:
            trigger_locator = modal.locator(
                "button",
                has_text=re.compile(r"please select a chunking method\\.", re.I),
            ).first

    if trigger_locator.count() == 0:
        if env_bool("PW_DEBUG_DUMP"):
            modal_text = modal.inner_text()
            button_count = modal.locator("button").count()
            label_count = modal.locator(
                "text=/please select a chunking method\\./i"
            ).count()
            debug(
                "[dataset] chunking_trigger_missing "
                f"button_count={button_count} label_count={label_count} "
                f"trigger_locator_count={trigger_locator.count()} "
                "trigger_handle_found=False"
            )
            debug(f"[dataset] modal_text_snippet={modal_text[:300]!r}")
        raise AssertionError("Chunking method dropdown trigger not found.")

    trigger_for_assert = trigger_locator
    expect(trigger_locator).to_be_visible(timeout=timeout_ms)
    try:
        trigger_locator.click()
    except Exception:
        trigger_locator.click(force=True)
    listbox = page.locator("[role='listbox']:visible").last
    if listbox.count() == 0:
        listbox = page.locator("[cmdk-list]:visible").last
    if listbox.count() == 0:
        listbox = page.locator("[data-state='open']:visible").last
    if listbox.count() == 0:
        listbox = page.locator("body").locator("div:visible").last

    option = listbox.locator("span", has_text=re.compile(r"^General$", re.I)).first
    if option.count() == 0:
        option = listbox.locator(
            "div", has=page.locator("span", has_text=re.compile(r"^General$", re.I))
        ).first
    if option.count() == 0 and env_bool("PW_DEBUG_DUMP"):
        try:
            listbox_text = listbox.inner_text()
        except Exception:
            listbox_text = ""
        span_count = listbox.locator(
            "span", has_text=re.compile(r"^General$", re.I)
        ).count()
        debug(
            "[dataset] general_option_missing "
            f"listbox_count={listbox.count()} span_count={span_count}"
        )
        debug(f"[dataset] listbox_text_snippet={listbox_text[:300]!r}")
    expect(option).to_be_visible(timeout=timeout_ms)
    option.click()
    if trigger_for_assert is not None:
        try:
            expect(trigger_for_assert).to_contain_text(
                re.compile(r"General", re.I), timeout=timeout_ms
            )
        except AssertionError:
            # Trigger can rerender after selection; verify selected label in modal instead.
            expect(modal).to_contain_text(re.compile(r"General", re.I), timeout=timeout_ms)