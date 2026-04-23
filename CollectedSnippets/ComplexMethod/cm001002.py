async def _execute(
        self,
        user_id: str | None,
        session: ChatSession,
        *,
        prompt: str = "",
        system_context: str = "",
        sub_autopilot_session_id: str = "",
        wait_for_result: int = 60,
        **kwargs,
    ) -> ToolResponseBase:
        if not prompt.strip():
            return ErrorResponse(
                message="prompt is required",
                session_id=session.session_id,
            )
        if user_id is None:
            return ErrorResponse(
                message="Authentication required",
                session_id=session.session_id,
            )

        # Resolve the sub's ChatSession id — either resume an owned one or
        # create a fresh session that inherits the parent's dry_run so a
        # sub spawned inside a dry-run conversation doesn't silently
        # escalate to a live run.
        sub_session_param = sub_autopilot_session_id.strip()
        if sub_session_param:
            owned = await get_chat_session(sub_session_param)
            if owned is None or owned.user_id != user_id:
                return ErrorResponse(
                    message=(
                        f"sub_autopilot_session_id {sub_session_param} is not "
                        "a session you own. Leave empty to start a fresh sub, "
                        "or pass a session_id returned by a previous "
                        "run_sub_session call of yours."
                    ),
                    session_id=session.session_id,
                )
            inner_session_id = sub_session_param
        else:
            new_session = await create_chat_session(user_id, dry_run=session.dry_run)
            inner_session_id = new_session.session_id

        effective_prompt = prompt
        if system_context.strip():
            effective_prompt = f"[System Context: {system_context.strip()}]\n\n{prompt}"

        cap = max(0, min(wait_for_result, MAX_SUB_SESSION_WAIT_SECONDS))
        started_at = time.monotonic()
        outcome, result = await run_copilot_turn_via_queue(
            session_id=inner_session_id,
            user_id=user_id,
            message=effective_prompt,
            timeout=cap,
            permissions=get_current_permissions(),
            tool_call_id=(f"sub:{session.session_id}" if session.session_id else "sub"),
            tool_name="run_sub_session",
        )
        elapsed = time.monotonic() - started_at
        return response_from_outcome(
            outcome=outcome,
            result=result,
            inner_session_id=inner_session_id,
            parent_session_id=session.session_id,
            elapsed=elapsed,
        )