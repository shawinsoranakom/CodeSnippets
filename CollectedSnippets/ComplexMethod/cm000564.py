async def execute_copilot(
        self,
        prompt: str,
        system_context: str,
        session_id: str,
        max_recursion_depth: int,
        user_id: str,
        permissions: "CopilotPermissions | None" = None,
    ) -> tuple[str, list[ToolCallEntry], str, str, TokenUsage]:
        """Invoke the copilot on the copilot_executor queue and aggregate the
        result.

        Delegates to :func:`run_copilot_turn_via_queue` — the shared
        primitive used by ``run_sub_session`` too — which creates the
        stream_registry meta record, enqueues the job, and waits on the
        Redis stream for the terminal event. Any available
        copilot_executor worker picks up the job, so this call survives
        the graph-executor worker dying mid-turn (RabbitMQ redelivers).

        Args:
            prompt: The user task/instruction.
            system_context: Optional context prepended to the prompt.
            session_id: Chat session to use.
            max_recursion_depth: Maximum allowed recursion nesting.
            user_id: Authenticated user ID.
            permissions: Optional capability filter restricting tools/blocks.

        Returns:
            A tuple of (response_text, tool_calls, history_json, session_id, usage).
        """
        from backend.copilot.sdk.session_waiter import (
            run_copilot_turn_via_queue,  # avoid circular import
        )

        tokens = _check_recursion(max_recursion_depth)
        perm_token = None
        try:
            effective_permissions, perm_token = _merge_inherited_permissions(
                permissions
            )
            effective_prompt = prompt
            if system_context:
                effective_prompt = f"[System Context: {system_context}]\n\n{prompt}"

            outcome, result = await run_copilot_turn_via_queue(
                session_id=session_id,
                user_id=user_id,
                message=effective_prompt,
                # Graph block execution is synchronous from the caller's
                # perspective — wait effectively as long as needed. The
                # SDK enforces its own idle-based timeout inside the
                # stream_registry pipeline.
                timeout=_AUTOPILOT_BLOCK_MAX_WAIT_SECONDS,
                permissions=effective_permissions,
                tool_call_id=_AUTOPILOT_TOOL_CALL_ID,
                tool_name=_AUTOPILOT_TOOL_NAME,
            )
            if outcome == "failed":
                raise RuntimeError(
                    "AutoPilot turn failed — see the session's transcript"
                )
            if outcome == "running":
                raise RuntimeError(
                    "AutoPilot turn did not complete within "
                    f"{_AUTOPILOT_BLOCK_MAX_WAIT_SECONDS}s — session "
                    f"{session_id}"
                )

            # Build a lightweight conversation summary from the aggregated data.
            # When ``result.queued`` is True the prompt rode on an already-
            # in-flight turn (``run_copilot_turn_via_queue`` queued it and
            # waited on the existing turn's stream); the aggregated result
            # is still valid, so the same rendering path applies.
            turn_messages: list[dict[str, Any]] = [
                {"role": "user", "content": effective_prompt},
            ]
            if result.tool_calls:
                turn_messages.append(
                    {
                        "role": "assistant",
                        "content": result.response_text,
                        "tool_calls": [tc.model_dump() for tc in result.tool_calls],
                    }
                )
            else:
                turn_messages.append(
                    {"role": "assistant", "content": result.response_text}
                )
            history_json = json.dumps(turn_messages, default=str)

            tool_calls: list[ToolCallEntry] = [
                {
                    "tool_call_id": tc.tool_call_id,
                    "tool_name": tc.tool_name,
                    "input": tc.input,
                    "output": tc.output,
                    "success": tc.success,
                }
                for tc in result.tool_calls
            ]

            usage: TokenUsage = {
                "prompt_tokens": result.prompt_tokens,
                "completion_tokens": result.completion_tokens,
                "total_tokens": result.total_tokens,
            }

            return (
                result.response_text,
                tool_calls,
                history_json,
                session_id,
                usage,
            )
        finally:
            _reset_recursion(tokens)
            if perm_token is not None:
                _inherited_permissions.reset(perm_token)