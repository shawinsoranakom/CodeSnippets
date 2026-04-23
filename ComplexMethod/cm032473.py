def select_cmdk_option_by_value_prefix(
    page,
    expect,
    combobox,
    value_prefix: str,
    option_text: str,
    list_testid: str,
    fallback_to_first: bool,
    timeout_ms: int,
) -> tuple[str, str | None]:
    """Select a cmdk option by value prefix or option text."""
    combobox.click()

    controls_id = combobox.get_attribute("aria-controls")
    options_container = None
    option_selector = (
        "[data-testid='combobox-option'], [role='option'], [cmdk-item], [data-value]"
    )

    if controls_id:
        controls_selector = f"[id={json.dumps(controls_id)}]:visible"
        scoped = page.locator(controls_selector)
        if scoped.count() > 0:
            options_container = scoped.first

    if options_container is None and list_testid:
        legacy_container = page.locator(f"[data-testid='{list_testid}']:visible")
        if legacy_container.count() > 0:
            options_container = legacy_container.first

    escaped_prefix = value_prefix.replace("'", "\\'")
    value_selector = f"[data-value^='{escaped_prefix}']"
    option_pattern = re.compile(rf"\b{re.escape(option_text)}\b", re.I)

    def options_locator():
        if options_container is not None:
            return options_container.locator(option_selector)
        return page.locator(option_selector)

    def option_locator():
        by_value = (
            options_container.locator(value_selector)
            if options_container is not None
            else page.locator(f"{value_selector}:visible")
        )
        if by_value.count() > 0:
            return by_value.first
        return options_locator().filter(has_text=option_pattern).first

    expect(options_locator().first).to_be_visible(timeout=timeout_ms)

    option = option_locator()
    if option.count() == 0:
        options = options_locator()
        if fallback_to_first and options.count() > 0:
            first_option = options.first
            selected_text = ""
            selected_value = None
            try:
                selected_text = first_option.inner_text().strip()
            except Exception:
                selected_text = ""
            try:
                selected_value = first_option.get_attribute("data-value")
            except Exception:
                selected_value = None
            click_with_retry(page, expect, lambda: first_option, attempts=3, timeout_ms=timeout_ms)
            if selected_text:
                expect(combobox).to_contain_text(
                    selected_text, timeout=timeout_ms
                )
            try:
                expect(combobox).to_have_attribute(
                    "aria-expanded", "false", timeout=timeout_ms
                )
            except AssertionError:
                page.keyboard.press("Escape")
                expect(combobox).to_have_attribute(
                    "aria-expanded", "false", timeout=timeout_ms
                )
            return selected_text or option_text, selected_value
        dump = []
        count = min(options.count(), 30)
        for i in range(count):
            item = options.nth(i)
            try:
                text = item.inner_text().strip()
            except Exception as exc:
                text = f"<text-error:{exc}>"
            try:
                data_value = item.get_attribute("data-value")
            except Exception as exc:
                data_value = f"<value-error:{exc}>"
            dump.append(f"{i + 1:02d}. text={text!r} data-value={data_value!r}")
        dump_text = "\n".join(dump)
        raise AssertionError(
            "No matching cmdk option found. "
            f"value_prefix={value_prefix!r} option_text={option_text!r} "
            f"list_testid={list_testid!r} aria_controls={controls_id!r} "
            f"options_count={options.count()}\n"
            f"options:\n{dump_text}"
        )

    selected_text = option_text
    try:
        selected_text = option.inner_text().strip() or option_text
    except Exception:
        selected_text = option_text
    selected_value = option.get_attribute("data-value")
    click_with_retry(page, expect, option_locator, attempts=3, timeout_ms=timeout_ms)
    expect(combobox).to_contain_text(selected_text, timeout=timeout_ms)
    try:
        expect(combobox).to_have_attribute("aria-expanded", "false", timeout=timeout_ms)
    except AssertionError:
        page.keyboard.press("Escape")
        expect(combobox).to_have_attribute("aria-expanded", "false", timeout=timeout_ms)
    return selected_text, selected_value