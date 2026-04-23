def _send_chat_and_wait_done(
    page, text: str, timeout_ms: int = 60000
) -> None:
    textarea = page.locator("[data-testid='chat-textarea']")
    expect(textarea).to_be_visible(timeout=RESULT_TIMEOUT_MS)
    tag_name = ""
    contenteditable = None
    try:
        tag_name = textarea.evaluate("el => el.tagName")
    except Exception:
        tag_name = ""
    try:
        contenteditable = textarea.get_attribute("contenteditable")
    except Exception:
        contenteditable = None

    is_input = tag_name in ("INPUT", "TEXTAREA")
    is_editable = is_input or contenteditable == "true"
    if not is_editable:
        raise AssertionError(
            "chat-textarea is not an editable element. "
            f"url={page.url} tag={tag_name!r} contenteditable={contenteditable!r}"
        )

    textarea.fill(text)
    typed_value = ""
    try:
        if is_input:
            typed_value = textarea.input_value()
        else:
            typed_value = textarea.inner_text()
    except Exception:
        typed_value = ""

    if text not in (typed_value or ""):
        textarea.click()
        page.keyboard.press("Control+A")
        page.keyboard.type(text)
        try:
            if is_input:
                typed_value = textarea.input_value()
            else:
                typed_value = textarea.inner_text()
        except Exception:
            typed_value = ""
        if text not in (typed_value or ""):
            raise AssertionError(
                "Failed to type prompt into chat-textarea. "
                f"url={page.url} tag={tag_name!r} contenteditable={contenteditable!r} "
                f"typed_value={typed_value!r}"
            )

    composer = textarea.locator("xpath=ancestor::form[1]")
    if composer.count() == 0:
        composer = textarea.locator("xpath=ancestor::div[1]")
    send_button = None
    if composer.count() > 0:
        if hasattr(composer, "get_by_role"):
            send_button = composer.get_by_role(
                "button", name=re.compile(r"send message", re.I)
            )
        if send_button is None or send_button.count() == 0:
            send_button = composer.locator(
                "button", has_text=re.compile(r"send message", re.I)
            )
    if send_button is not None and send_button.count() > 0:
        send_button.first.click()
        send_used = True
    else:
        textarea.press("Enter")
        send_used = False

    status_marker = page.locator("[data-testid='chat-stream-status']").first
    try:
        expect(status_marker).to_have_attribute(
            "data-status", "idle", timeout=timeout_ms
        )
    except Exception as exc:
        try:
            # Some UI builds remove the stream-status marker when generation finishes.
            expect(page.locator("[data-testid='chat-stream-status']")).to_have_count(
                0, timeout=timeout_ms
            )
            return
        except Exception:
            pass
        try:
            marker_count = page.locator("[data-testid='chat-stream-status']").count()
        except Exception:
            marker_count = -1
        try:
            status_value = status_marker.get_attribute("data-status")
        except Exception:
            status_value = None
        raise AssertionError(
            "Chat stream status marker not idle within timeout. "
            f"url={page.url} marker_count={marker_count} status={status_value!r} "
            f"tag={tag_name!r} contenteditable={contenteditable!r} "
            f"typed_value={typed_value!r} send_button_used={send_used}"
        ) from exc