async def wrapper(args: dict[str, Any]) -> dict[str, Any]:
        # Detect empty-args truncation: args is empty AND the schema declares
        # at least one property (so a non-empty call was expected).
        # NOTE: _build_input_schema intentionally omits "required" to avoid
        # SDK-side validation rejecting truncated calls before reaching this
        # handler.  We detect truncation via "properties" instead.
        schema_has_params = bool(input_schema and input_schema.get("properties"))
        if not args and schema_has_params:
            logger.warning(
                "[MCP] %s called with empty args (likely output "
                "token truncation) — returning guidance",
                tool_name,
            )
            return _mcp_error(
                f"Your call to {tool_name} had empty arguments — "
                f"this means your previous response was too long and "
                f"the tool call input was truncated by the API. "
                f"To fix this: break your work into smaller steps. "
                f"For large content, first write it to a file using "
                f"bash_exec with cat >> (append section by section), "
                f"then pass it via @@agptfile:filename reference. "
                f"Do NOT retry with the same approach — it will "
                f"be truncated again."
            )

        original_args = args
        stop_msg = _check_circuit_breaker(tool_name, original_args)
        if stop_msg:
            return _mcp_error(stop_msg)

        user_id, session = get_execution_context()
        if session is not None:
            try:
                args = await expand_file_refs_in_args(
                    args, user_id, session, input_schema=input_schema
                )
            except FileRefExpansionError as exc:
                _record_tool_failure(tool_name, original_args)
                return _mcp_error(
                    f"@@agptfile: reference could not be resolved: {exc}. "
                    "Ensure the file exists before referencing it. "
                    "For sandbox paths use bash_exec to verify the file exists first; "
                    "for workspace files use a workspace:// URI."
                )
        result = await fn(args)
        truncated = truncate(result, _MCP_MAX_CHARS)

        if truncated.get("isError"):
            _record_tool_failure(tool_name, original_args)
        else:
            _clear_tool_failures(tool_name)

        # Stash the raw tool output for the frontend SSE stream so widgets
        # (bash, tool viewers) receive clean JSON.  Mid-turn user follow-up
        # injection for MCP + built-in tools is now handled uniformly by
        # the ``PostToolUse`` hook via ``additionalContext`` so Claude sees
        # the follow-up attached to the tool_result without mutating the
        # frontend-facing payload.
        if not truncated.get("isError"):
            text = _text_from_mcp_result(truncated)
            if text:
                stash_pending_tool_output(tool_name, text)

        # Strip is_dry_run only when the session itself is in dry_run mode.
        # In that case the LLM must not know it is simulating — it should act
        # as if every tool call produced real results.
        # In normal (non-session-dry_run) mode, is_dry_run=True is intentionally
        # left visible to the LLM so it knows a specific tool was simulated and
        # can reason about the reliability of that output.
        if session is not None and session.dry_run:
            truncated = _strip_llm_fields(truncated)

        return truncated