def step_06_run_agent(
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
    require(flow_state, "agent_detail_open")
    page = flow_page
    with step("run agent"):
        import os

        run_ui_timeout_ms = int(os.getenv("PW_AGENT_RUN_UI_TIMEOUT_MS", "60000"))
        run_root = page.locator("[data-testid='agent-run']")
        run_ui_selector = (
            "[data-testid='agent-run-chat'], "
            "[data-testid='chat-textarea'], "
            "[data-testid='agent-run-idle']"
        )
        run_ui_locator = page.locator(run_ui_selector)

        try:
            if run_ui_locator.count() > 0 and run_ui_locator.first.is_visible():
                flow_state["agent_running"] = True
                snap("agent_run_already_open")
                return
        except Exception:
            pass

        if run_root.count() == 0:
            run_button = page.get_by_role("button", name=re.compile(r"^run$", re.I))
        else:
            run_button = run_root
        expect(run_button).to_be_visible(timeout=RESULT_TIMEOUT_MS)
        run_attempts = max(1, int(os.getenv("PW_AGENT_RUN_ATTEMPTS", "2")))
        last_error = None
        for attempt in range(run_attempts):
            if attempt > 0:
                page.wait_for_timeout(500)
            try:
                auth_click(run_button, f"agent_run_attempt_{attempt + 1}")
            except Exception as exc:
                last_error = exc
                continue
            try:
                run_ui_locator.first.wait_for(state="visible", timeout=run_ui_timeout_ms)
                flow_state["agent_running"] = True
                snap("agent_run_started")
                return
            except Exception as exc:
                last_error = exc

        suffix = f" last_error={last_error}" if last_error else ""
        _raise_with_diagnostics(
            page,
            f"Agent run UI did not open after clicking Run ({run_attempts} attempts).{suffix}",
            snap=snap,
            snap_name="agent_run_missing",
        )