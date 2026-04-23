def step_07_send_chat(
    flow_page,
    flow_state,
    base_url,
    login_url,
    active_auth_context,
    step,
    snap,
    auth_click,
    seeded_user_credentials,
):
    require(flow_state, "agent_running")
    page = flow_page
    with step("send agent chat"):
        dataset_combobox = page.locator("[data-testid='chat-datasets-combobox']")
        if dataset_combobox.count() > 0:
            try:
                if dataset_combobox.is_visible():
                    dataset_combobox.click()
                    options = page.locator("[data-testid='datasets-options']")
                    expect(options).to_be_visible(timeout=RESULT_TIMEOUT_MS)
                    option = page.locator("[data-testid='datasets-option-0']")
                    if option.count() == 0:
                        option = page.locator("[data-testid^='datasets-option-']").first
                    if option.count() > 0 and option.is_visible():
                        try:
                            flow_state["dataset_label"] = option.inner_text()
                        except Exception:
                            flow_state["dataset_label"] = ""
                        option.click()
                        flow_state["dataset_selected"] = True
            except Exception:
                pass

        textarea = page.locator("[data-testid='chat-textarea']")
        idle_marker = page.locator("[data-testid='agent-run-idle']")
        try:
            expect(textarea).to_be_visible(timeout=RESULT_TIMEOUT_MS)
        except AssertionError:
            _raise_with_diagnostics(
                page,
                "Chat textarea not visible in agent run UI.",
                snap=snap,
                snap_name="agent_run_chat_missing",
            )

        textarea.fill("say hello")
        textarea.press("Enter")
        try:
            expect(idle_marker).to_be_visible(timeout=60000)
        except AssertionError:
            # Older UI builds do not expose agent-run-idle; fallback to assistant reply.
            agent_chat = page.locator("[data-testid='agent-run-chat']")
            assistant_reply = agent_chat.locator(
                "text=/how can i assist|hello/i"
            ).first
            try:
                expect(assistant_reply).to_be_visible(timeout=60000)
            except AssertionError:
                _raise_with_diagnostics(
                    page,
                    "Agent run chat did not return to idle state after sending message.",
                    snap=snap,
                    snap_name="agent_run_idle_missing",
                )
    snap("agent_run_idle_restored")