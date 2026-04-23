def _check_empty_tool_breaker(
    sdk_msg: object,
    consecutive: int,
    ctx: _StreamContext,
    state: _RetryState,
) -> _EmptyToolBreakResult:
    """Detect consecutive empty tool calls and trip the circuit breaker.

    Returns an ``_EmptyToolBreakResult`` with the updated counter and, if the
    breaker tripped, the ``StreamError`` to yield plus the error metadata.
    """
    if not isinstance(sdk_msg, AssistantMessage):
        return _EmptyToolBreakResult(consecutive, False, None, None, None)

    empty_tools = [
        b.name for b in sdk_msg.content if isinstance(b, ToolUseBlock) and not b.input
    ]
    if not empty_tools:
        # Reset on any non-empty-tool AssistantMessage (including text-only
        # messages — any() over empty content is False).
        return _EmptyToolBreakResult(0, False, None, None, None)

    consecutive += 1

    # Log full diagnostics on first occurrence only; subsequent hits just
    # log the counter to reduce noise.
    if consecutive == 1:
        logger.warning(
            "%s Empty tool call detected (%d/%d): "
            "tools=%s, model=%s, error=%s, "
            "block_types=%s, cumulative_usage=%s",
            ctx.log_prefix,
            consecutive,
            _EMPTY_TOOL_CALL_LIMIT,
            empty_tools,
            sdk_msg.model,
            sdk_msg.error,
            [type(b).__name__ for b in sdk_msg.content],
            {
                "prompt": state.usage.prompt_tokens,
                "completion": state.usage.completion_tokens,
                "cache_read": state.usage.cache_read_tokens,
            },
        )
    else:
        logger.warning(
            "%s Empty tool call detected (%d/%d): tools=%s",
            ctx.log_prefix,
            consecutive,
            _EMPTY_TOOL_CALL_LIMIT,
            empty_tools,
        )

    if consecutive < _EMPTY_TOOL_CALL_LIMIT:
        return _EmptyToolBreakResult(consecutive, False, None, None, None)

    logger.error(
        "%s Circuit breaker: aborting stream after %d "
        "consecutive empty tool calls. "
        "This is likely caused by the model attempting "
        "to write content too large for a single tool "
        "call's output token limit. The model should "
        "write large files in chunks using bash_exec "
        "with cat >> (append).",
        ctx.log_prefix,
        consecutive,
    )
    error_msg = _CIRCUIT_BREAKER_ERROR_MSG
    error_code = "circuit_breaker_empty_tool_calls"
    _append_error_marker(ctx.session, error_msg, retryable=True)
    return _EmptyToolBreakResult(
        count=consecutive,
        tripped=True,
        error=StreamError(errorText=error_msg, code=error_code),
        error_msg=error_msg,
        error_code=error_code,
    )