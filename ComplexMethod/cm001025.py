async def _execute(
        self,
        user_id: str | None,
        session: ChatSession,
        action: str = "",
        target: str = "",
        value: str = "",
        direction: str = "down",
        **kwargs: Any,
    ) -> ToolResponseBase:
        """Perform a browser action and return an updated page snapshot.

        Validates the *action*/*target*/*value* combination, delegates to
        ``agent-browser``, waits for the page to settle, and returns the
        accessibility-tree snapshot so the LLM can plan the next step.
        """
        action = action.strip()
        target = target.strip()
        value = value.strip()
        direction = direction.strip()
        session_name = session.session_id

        if not action:
            return ErrorResponse(
                message="Please specify an action.",
                error="missing_action",
                session_id=session_name,
            )

        # Build the agent-browser command args
        if action in _NO_TARGET_ACTIONS:
            cmd_args = [action]

        elif action in _SCROLL_ACTIONS:
            cmd_args = ["scroll", direction]

        elif action == "press":
            if not value:
                return ErrorResponse(
                    message="'press' requires a 'value' (key name, e.g. 'Enter').",
                    error="missing_value",
                    session_id=session_name,
                )
            cmd_args = ["press", value]

        elif action in _TARGET_ONLY_ACTIONS:
            if not target:
                return ErrorResponse(
                    message=f"'{action}' requires a 'target' element.",
                    error="missing_target",
                    session_id=session_name,
                )
            cmd_args = [action, target]

        elif action in _TARGET_VALUE_ACTIONS:
            if not target or not value:
                return ErrorResponse(
                    message=f"'{action}' requires both 'target' and 'value'.",
                    error="missing_params",
                    session_id=session_name,
                )
            cmd_args = [action, target, value]

        elif action in _WAIT_ACTIONS:
            if not target:
                return ErrorResponse(
                    message=(
                        "'wait' requires a 'target': a CSS selector to wait for, "
                        "or milliseconds as a string (e.g. '1000')."
                    ),
                    error="missing_target",
                    session_id=session_name,
                )
            cmd_args = ["wait", target]

        else:
            return ErrorResponse(
                message=f"Unsupported action: {action}",
                error="invalid_action",
                session_id=session_name,
            )

        # Restore browser state from cloud if this is a different pod
        if user_id:
            await _ensure_session(session_name, user_id, session)

        rc, _, stderr = await _run(session_name, *cmd_args)
        if rc != 0:
            logger.warning("[browser_act] %s failed: %s", action, stderr[:300])
            return ErrorResponse(
                message=f"Action '{action}' failed.",
                error="action_failed",
                session_id=session_name,
            )

        # Allow the page to settle after interaction (best-effort: SPAs may not idle)
        settle_rc, _, settle_err = await _run(
            session_name, "wait", "--load", "networkidle"
        )
        if settle_rc != 0:
            logger.warning(
                "[browser_act] post-action wait failed: %s", settle_err[:300]
            )

        snapshot = await _snapshot(session_name)
        _, url_out, _ = await _run(session_name, "get", "url")

        result = BrowserActResponse(
            message=f"Performed '{action}'" + (f" on '{target}'" if target else ""),
            action=action,
            current_url=url_out.strip(),
            snapshot=snapshot,
            session_id=session_name,
        )

        # Persist browser state to cloud for cross-pod continuity
        if user_id:
            _fire_and_forget_save(session_name, user_id, session)

        return result