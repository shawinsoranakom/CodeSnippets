def mm_step_12_composer_and_single_send(ctx: FlowContext, step, snap):
    require(ctx.state, "mm_cards_configured", "mm_selected_option_testids", "mm_option_prefix")
    page = ctx.page
    selected_option_testids = ctx.state["mm_selected_option_testids"]
    option_prefix = ctx.state["mm_option_prefix"]
    completion_payloads: list[dict] = []

    def _on_completion_request(req):
        if (
            req.method.upper() in MM_REQUEST_METHOD_WHITELIST
            and "/api/v1/chats/" in req.url
            and "/sessions/" in req.url
            and req.url.rstrip("/").endswith("/completions")
        ):
            completion_payloads.append(_mm_payload_from_request(req))

    with step("composer interactions and single send in multi-model mode"):
        attach_path = Path(gettempdir()) / f"chat-detail-attach-{int(time() * 1000)}.txt"
        attach_path.write_text("chat-detail-attachment", encoding="utf-8")
        try:
            try:
                with page.expect_file_chooser(timeout=5000) as chooser_info:
                    page.get_by_test_id("chat-detail-attach").click()
                chooser_info.value.set_files(str(attach_path))
            except PlaywrightTimeoutError:
                file_input = page.locator("input[type='file']").first
                expect(file_input).to_be_attached(timeout=RESULT_TIMEOUT_MS)
                file_input.set_input_files(str(attach_path))
            expect(page.locator(f"text={attach_path.name}").first).to_be_visible(
                timeout=RESULT_TIMEOUT_MS
            )

            thinking_toggle = page.get_by_test_id("chat-detail-thinking-toggle")
            expect(thinking_toggle).to_be_visible(timeout=RESULT_TIMEOUT_MS)
            thinking_class_before = thinking_toggle.get_attribute("class") or ""
            thinking_toggle.click()
            thinking_class_after = thinking_toggle.get_attribute("class") or ""
            assert thinking_class_after != thinking_class_before

            internet_toggle = page.get_by_test_id("chat-detail-internet-toggle")
            if internet_toggle.count() > 0:
                expect(internet_toggle).to_be_visible(timeout=RESULT_TIMEOUT_MS)
                internet_class_before = internet_toggle.get_attribute("class") or ""
                internet_toggle.click()
                internet_class_after = internet_toggle.get_attribute("class") or ""
                assert internet_class_after != internet_class_before

            audio_toggle = page.get_by_test_id("chat-detail-audio-toggle")
            if audio_toggle.count() > 0:
                expect(audio_toggle).to_be_visible(timeout=RESULT_TIMEOUT_MS)
                expect(audio_toggle).to_be_enabled(timeout=RESULT_TIMEOUT_MS)
                audio_toggle.focus()
                expect(audio_toggle).to_be_focused(timeout=RESULT_TIMEOUT_MS)

            page.on("request", _on_completion_request)
            prompt = f"multi model send {int(time())}"
            textarea = page.get_by_test_id("chat-textarea")
            textarea.fill(prompt)
            send_btn = page.get_by_test_id("chat-detail-send")
            expect(send_btn).to_be_enabled(timeout=RESULT_TIMEOUT_MS)
            send_btn.click()

            stream_status = page.get_by_test_id("chat-stream-status")
            try:
                expect(stream_status).to_be_visible(timeout=5000)
            except AssertionError:
                pass
            try:
                expect(stream_status.first).to_have_attribute(
                    "data-status", "idle", timeout=90000
                )
            except AssertionError:
                expect(stream_status).to_have_count(0, timeout=90000)

            deadline = monotonic() + 8
            while not completion_payloads and monotonic() < deadline:
                page.wait_for_timeout(100)
        finally:
            page.remove_listener("request", _on_completion_request)
            attach_path.unlink(missing_ok=True)

        assert completion_payloads, "no chat session completion request was captured"
        payloads_with_messages = [p for p in completion_payloads if p.get("messages")]
        assert payloads_with_messages, "completion requests did not include messages"

        selected_model_ids = [
            tid.replace(option_prefix, "")
            for tid in selected_option_testids
            if tid.startswith(option_prefix)
        ]
        has_model_payload = any(
            (p.get("llm_id") in selected_model_ids)
            or ("llm_id" in p)
            or any(
                k in p
                for k in (
                    "temperature",
                    "top_p",
                    "presence_penalty",
                    "frequency_penalty",
                    "max_tokens",
                )
            )
            for p in payloads_with_messages
        )
        assert has_model_payload, "no completion payload carried model-specific fields"

    ctx.state["mm_single_send_done"] = True
    snap("chat_mm_single_send_done")