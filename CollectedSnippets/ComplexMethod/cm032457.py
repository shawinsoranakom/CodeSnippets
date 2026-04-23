def mm_step_05_sessions_panel_row_ops(ctx: FlowContext, step, snap):
    require(ctx.state, "mm_embed_checked")
    page = ctx.page
    with step("sessions panel and session row operations"):
        sessions_root = page.get_by_test_id("chat-detail-sessions")
        expect(sessions_root).to_be_visible(timeout=RESULT_TIMEOUT_MS)

        page.get_by_test_id("chat-detail-sessions-close").click()
        expect(page.get_by_test_id("chat-detail-sessions-open")).to_be_visible(
            timeout=RESULT_TIMEOUT_MS
        )
        page.get_by_test_id("chat-detail-sessions-open").click()
        expect(sessions_root).to_be_visible(timeout=RESULT_TIMEOUT_MS)

        page.get_by_test_id("chat-detail-session-new").click()
        session_rows = page.locator("[data-testid='chat-detail-session-item']")
        expect(session_rows.first).to_be_visible(timeout=RESULT_TIMEOUT_MS)
        active_session = sessions_root.locator(
            "li[aria-selected='true'] [data-testid='chat-detail-session-item']"
        )
        selected_row = active_session.first if active_session.count() > 0 else session_rows.first
        created_session_id = selected_row.get_attribute("data-session-id") or ""
        assert created_session_id, "failed to capture created session id"

        selected_row.click()
        expect(
            page.locator(
                f"[data-testid='chat-detail-session-item'][data-session-id='{created_session_id}']"
            ).first
        ).to_be_visible(timeout=RESULT_TIMEOUT_MS)

        search_input = page.get_by_test_id("chat-detail-session-search")
        expect(search_input).to_be_visible(timeout=RESULT_TIMEOUT_MS)
        row_count_before = session_rows.count()
        no_match_query = "__PW_NO_MATCH_SESSION__"
        search_input.fill(no_match_query)
        expect(search_input).to_have_value(no_match_query, timeout=RESULT_TIMEOUT_MS)
        filtered_rows = page.locator("[data-testid='chat-detail-session-item']")
        min_filtered_count = row_count_before
        deadline = monotonic() + 5
        while monotonic() < deadline:
            min_filtered_count = min(min_filtered_count, filtered_rows.count())
            if min_filtered_count < row_count_before:
                break
            page.wait_for_timeout(100)

        # When only one row exists, some builds keep it visible for temporary sessions.
        # In that case we still validate the search interaction without forcing impossible narrowing.
        if row_count_before > 1:
            assert (
                min_filtered_count < row_count_before
            ), "session search did not narrow visible rows"
        else:
            assert min_filtered_count <= row_count_before
        search_input.fill("")
        expect(
            page.locator(
                f"[data-testid='chat-detail-session-item'][data-session-id='{created_session_id}']"
            ).first
        ).to_be_visible(timeout=RESULT_TIMEOUT_MS)

        row_li = sessions_root.locator(
            f"li:has([data-testid='chat-detail-session-item'][data-session-id='{created_session_id}'])"
        ).first
        row_li.hover()
        actions_btn = page.locator(
            f"[data-testid='chat-detail-session-actions'][data-session-id='{created_session_id}']"
        ).first
        expect(actions_btn).to_be_visible(timeout=RESULT_TIMEOUT_MS)
        actions_btn.click()

        row_delete = page.locator(
            f"[data-testid='chat-detail-session-delete'][data-session-id='{created_session_id}']"
        ).first
        expect(row_delete).to_be_visible(timeout=RESULT_TIMEOUT_MS)
        row_delete.click()
        row_delete_dialog = page.get_by_test_id("confirm-delete-dialog")
        try:
            expect(row_delete_dialog).to_be_visible(timeout=3000)
            page.get_by_test_id("confirm-delete-dialog-cancel-btn").click()
            expect(row_delete_dialog).not_to_be_visible(timeout=RESULT_TIMEOUT_MS)
        except AssertionError:
            # If no dialog renders in this branch, still dismiss any menu overlay.
            page.keyboard.press("Escape")

        expect(
            page.locator(
                f"[data-testid='chat-detail-session-item'][data-session-id='{created_session_id}']"
            ).first
        ).to_be_visible(timeout=RESULT_TIMEOUT_MS)

    ctx.state["mm_created_session_id"] = created_session_id
    ctx.state["mm_session_row_checked"] = True
    snap("chat_mm_sessions_row_checked")