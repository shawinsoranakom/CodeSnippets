def select_default_model(
    page,
    expect,
    combobox,
    value_prefix: str,
    option_text: str,
    list_testid: str,
    fallback_to_first: bool,
    timeout_ms: int,
) -> tuple[str, str | None]:
    """Select and persist a default model."""
    if not needs_selection(combobox, value_prefix, option_text):
        try:
            current_text = combobox.inner_text().strip()
        except Exception:
            current_text = option_text
        return current_text, None

    selected = ("", None)

    def trigger():
        nonlocal selected
        selected = select_cmdk_option_by_value_prefix(
            page,
            expect,
            combobox,
            value_prefix,
            option_text,
            list_testid,
            fallback_to_first=fallback_to_first,
            timeout_ms=timeout_ms,
        )

    try:
        capture_response(
            page,
            trigger,
            lambda resp: resp.request.method == "POST"
            and "/v1/user/set_tenant_info" in resp.url,
        )
    except PlaywrightTimeoutError:
        if not selected[0]:
            raise

    _assert_selected_option_value(selected[1], value_prefix, option_text)

    expected_text = selected[0] or option_text
    expect(combobox).to_contain_text(expected_text, timeout=timeout_ms)
    try:
        current_text = combobox.inner_text().strip()
    except Exception:
        current_text = expected_text
    if _has_malformed_model_suffix(current_text):
        raise AssertionError(
            "Combobox text still contains malformed model suffix '#': "
            f"text={current_text!r} expected={expected_text!r}"
        )
    return selected