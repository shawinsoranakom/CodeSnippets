def mm_step_06_selection_mode_batch_delete(ctx: FlowContext, step, snap):
    require(ctx.state, "mm_session_row_checked", "mm_created_session_id")
    page = ctx.page
    created_session_id = ctx.state["mm_created_session_id"]
    with step("selection mode and batch delete cancel + confirm"):
        sessions_root = page.get_by_test_id("chat-detail-sessions")
        if sessions_root.count() == 0 or not sessions_root.is_visible():
            page.get_by_test_id("chat-detail-sessions-open").click()
        expect(sessions_root).to_be_visible(timeout=RESULT_TIMEOUT_MS)

        selection_enable = page.get_by_test_id("chat-detail-session-selection-enable")
        expect(selection_enable).to_be_visible(timeout=RESULT_TIMEOUT_MS)
        try:
            selection_enable.click(timeout=5000)
        except PlaywrightTimeoutError:
            page.keyboard.press("Escape")
            page.mouse.click(5, 5)
            selection_enable.click(timeout=RESULT_TIMEOUT_MS)
        checked_before = page.locator(
            "[data-testid='chat-detail-session-checkbox'][data-state='checked']"
        ).count()
        page.get_by_test_id("chat-detail-session-select-all").click()
        checked_after = page.locator(
            "[data-testid='chat-detail-session-checkbox'][data-state='checked']"
        ).count()
        if page.locator("[data-testid='chat-detail-session-checkbox']").count() > 1:
            assert checked_after != checked_before
        else:
            assert checked_after >= checked_before

        session_checkbox = page.locator(
            f"[data-testid='chat-detail-session-checkbox'][data-session-id='{created_session_id}']"
        ).first
        expect(session_checkbox).to_be_visible(timeout=RESULT_TIMEOUT_MS)
        if _mm_is_checked(session_checkbox):
            session_checkbox.click()
            assert not _mm_is_checked(session_checkbox)
        session_checkbox.click()
        assert _mm_is_checked(session_checkbox), "target session checkbox did not become checked"

        page.get_by_test_id("chat-detail-session-selection-exit").click()
        expect(
            page.locator(
                f"[data-testid='chat-detail-session-item'][data-session-id='{created_session_id}']"
            ).first
        ).to_be_visible(timeout=RESULT_TIMEOUT_MS)

        selection_enable = page.get_by_test_id("chat-detail-session-selection-enable")
        expect(selection_enable).to_be_visible(timeout=RESULT_TIMEOUT_MS)
        try:
            selection_enable.click(timeout=5000)
        except PlaywrightTimeoutError:
            page.keyboard.press("Escape")
            page.mouse.click(5, 5)
            selection_enable.click(timeout=RESULT_TIMEOUT_MS)
        session_checkbox = page.locator(
            f"[data-testid='chat-detail-session-checkbox'][data-session-id='{created_session_id}']"
        ).first
        expect(session_checkbox).to_be_visible(timeout=RESULT_TIMEOUT_MS)
        if not _mm_is_checked(session_checkbox):
            session_checkbox.click()

        page.get_by_test_id("chat-detail-session-batch-delete").click()
        batch_dialog = page.get_by_test_id("chat-detail-session-batch-delete-dialog")
        expect(batch_dialog).to_be_visible(timeout=RESULT_TIMEOUT_MS)
        page.get_by_test_id("chat-detail-session-batch-delete-cancel").click()
        expect(batch_dialog).not_to_be_visible(timeout=RESULT_TIMEOUT_MS)
        expect(
            page.locator(
                f"[data-testid='chat-detail-session-checkbox'][data-session-id='{created_session_id}']"
            ).first
        ).to_be_visible(timeout=RESULT_TIMEOUT_MS)

        page.get_by_test_id("chat-detail-session-batch-delete").click()
        expect(batch_dialog).to_be_visible(timeout=RESULT_TIMEOUT_MS)
        page.get_by_test_id("chat-detail-session-batch-delete-confirm").click()
        expect(batch_dialog).not_to_be_visible(timeout=RESULT_TIMEOUT_MS)
        expect(
            page.locator(
                f"[data-testid='chat-detail-session-item'][data-session-id='{created_session_id}']"
            )
        ).to_have_count(0, timeout=RESULT_TIMEOUT_MS)
        expect(
            sessions_root.locator(
                "li[aria-selected='true'] "
                f"[data-testid='chat-detail-session-item'][data-session-id='{created_session_id}']"
            )
        ).to_have_count(0, timeout=RESULT_TIMEOUT_MS)

    ctx.state["mm_sessions_cleanup_done"] = True
    snap("chat_mm_sessions_cleanup_done")