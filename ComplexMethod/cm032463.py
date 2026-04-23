def step_03_submit_registration(
    flow_page,
    flow_state,
    login_url,
    active_auth_context,
    step,
    snap,
    auth_debug_dump,
    auth_click,
    reg_email,
    reg_email_generator,
    reg_password,
    reg_nickname,
    reg_email_unique,
):
    require(flow_state, "login_opened", "register_toggle_available")
    page = flow_page
    form, _ = active_auth_context()
    nickname_input = form.locator(NICKNAME_INPUT)
    if nickname_input.count() == 0:
        pytest.skip("Register form not active; cannot submit registration.")

    email_input = form.locator(EMAIL_INPUT)
    password_input = form.locator(PASSWORD_INPUT)

    current_email = reg_email
    with step("fill registration form"):
        expect(email_input).to_have_count(1)
        expect(password_input).to_have_count(1)
        nickname_input.fill(reg_nickname)
        email_input.fill(current_email)
        password_input.fill(reg_password)
        expect(password_input).to_have_attribute("type", "password")
        password_input.blur()
    snap("filled")

    retried = False
    while True:
        with step("submit registration and wait for response"):
            form, _ = active_auth_context()
            submit_button = form.locator(SUBMIT_BUTTON)
            expect(submit_button).to_have_count(1)
            if not retried:
                snap("before_submit_click")
                auth_debug_dump("before_submit_click", submit_button)

            try:
                response_info = capture_response_json(
                    page,
                    lambda: (
                        auth_click(
                            submit_button,
                            "submit_register_retry" if retried else "submit_register",
                        ),
                        snap("retry_submitted" if retried else "submitted"),
                    ),
                    lambda resp: resp.request.method == "POST"
                    and "/v1/user/register" in resp.url,
                    timeout_ms=RESULT_TIMEOUT_MS,
                )
            except PlaywrightTimeoutError as exc:
                snap("failure")
                raise AssertionError(
                    f"Register response not received in time. url={page.url} email={current_email}"
                ) from exc

        _debug_register_response(page, response_info)

        if response_info.get("code") == 0:
            snap("registered_success_response")
            form, _ = active_auth_context()
            nickname_input = form.locator(NICKNAME_INPUT)
            expect(nickname_input).to_have_count(0, timeout=RESULT_TIMEOUT_MS)
            break

        snap("registered_error_response")
        message_text = response_info.get("message", "") or ""
        if _is_already_registered(message_text) and not retried:
            retried = True
            with step("retry registration with new email"):
                _wait_for_auth_not_loading(page)
                form, _ = active_auth_context()
                email_input = form.locator(EMAIL_INPUT)
                expect(email_input).to_have_count(1)
                current_email = reg_email_generator(force_unique=True)
                email_input.fill(current_email)
                snap("retry_filled")
            continue

        snap("failure")
        raise AssertionError(
            "Registration error detected. "
            f"url={response_info.get('__url__')} status={response_info.get('__status__')} "
            f"code={response_info.get('code')} message={response_info.get('message')} "
            f"email={current_email}"
        )

    snap("success")
    flow_state["register_complete"] = True
    flow_state["registered_email"] = current_email
    print(f"REGISTERED_EMAIL={current_email}", flush=True)