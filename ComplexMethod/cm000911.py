def _dispatch_response(
    response: StreamBaseResponse,
    acc: _StreamAccumulator,
    ctx: "_StreamContext",
    state: "_RetryState",
    entries_replaced: bool,
    log_prefix: str,
    skip_strip: bool = False,
) -> StreamBaseResponse | None:
    """Process a single adapter response and update session/accumulator state.

    Returns the response to yield to the client, or `None` if the response
    should be suppressed (e.g. `StreamStart` duplicates).

    Handles:
    - Logging tool events and errors
    - Persisting error markers
    - Accumulating text deltas into `assistant_response`
    - Appending tool input/output to session messages and transcript
    - Detecting `StreamFinish`

    Args:
        skip_strip: When True, bypass ThinkingStripper.process() for this delta.
            Used for the flushed tail delta which is already stripped content.
    """
    if isinstance(response, StreamStart):
        return None

    if isinstance(
        response,
        (StreamToolInputAvailable, StreamToolOutputAvailable),
    ):
        extra = ""
        if isinstance(response, StreamToolOutputAvailable):
            out_len = len(str(response.output))
            extra = f", output_len={out_len}"
        logger.info(
            "%s Tool event: %s, tool=%s%s",
            log_prefix,
            type(response).__name__,
            getattr(response, "toolName", "N/A"),
            extra,
        )

    # Persist error markers so they survive page refresh
    if isinstance(response, StreamError):
        logger.error(
            "%s Sending error to frontend: %s (code=%s)",
            log_prefix,
            response.errorText,
            response.code,
        )
        _append_error_marker(
            ctx.session,
            response.errorText,
            retryable=(response.code == "transient_api_error"),
        )

    if isinstance(response, StreamReasoningStart):
        acc.reasoning_response = ChatMessage(role="reasoning", content="")
        ctx.session.messages.append(acc.reasoning_response)

    elif isinstance(response, StreamReasoningDelta):
        if acc.reasoning_response is not None:
            acc.reasoning_response.content = (acc.reasoning_response.content or "") + (
                response.delta or ""
            )

    elif isinstance(response, StreamReasoningEnd):
        acc.reasoning_response = None

    elif isinstance(response, StreamTextDelta):
        raw_delta = response.delta or ""
        if skip_strip:
            # Pre-stripped tail from ThinkingStripper.flush() — bypass process()
            # to avoid re-suppressing content that looks like a partial tag opener.
            delta = raw_delta
        else:
            # Strip <internal_reasoning> / <thinking> tags that non-extended-
            # thinking models (e.g. Sonnet) may emit as visible text.
            delta = acc.thinking_stripper.process(raw_delta)
            if not delta:
                # Stripper is buffering a potential tag — suppress this event.
                return None
        # Replace the delta with the stripped version for the SSE client.
        response = StreamTextDelta(id=response.id, delta=delta)
        if acc.has_tool_results and acc.has_appended_assistant:
            acc.assistant_response = ChatMessage(role="assistant", content=delta)
            acc.accumulated_tool_calls = []
            acc.has_appended_assistant = False
            acc.has_tool_results = False
            ctx.session.messages.append(acc.assistant_response)
            acc.has_appended_assistant = True
        else:
            acc.assistant_response.content = (
                acc.assistant_response.content or ""
            ) + delta
            if not acc.has_appended_assistant:
                ctx.session.messages.append(acc.assistant_response)
                acc.has_appended_assistant = True

    elif isinstance(response, StreamToolInputAvailable):
        acc.accumulated_tool_calls.append(
            {
                "id": response.toolCallId,
                "type": "function",
                "function": {
                    "name": response.toolName,
                    "arguments": json.dumps(response.input or {}),
                },
            }
        )
        acc.assistant_response.tool_calls = acc.accumulated_tool_calls
        if not acc.has_appended_assistant:
            ctx.session.messages.append(acc.assistant_response)
            acc.has_appended_assistant = True

    elif isinstance(response, StreamToolOutputAvailable):
        # Dedupe: the response adapter can emit the same tool_use_id more than
        # once when the CLI re-delivers a ToolResultBlock (e.g. after a retry
        # or when a parallel-tool UserMessage is processed alongside a flush).
        # Guard at persistence time — the first emission already wrote the row
        # (via the pop_pending_tool_output stash, so it has clean text), and a
        # duplicate would land a second row with the raw MCP list fallback
        # content (breaking frontend widgets and inflating conversation tokens).
        already_persisted = any(
            m.role == "tool" and m.tool_call_id == response.toolCallId
            for m in ctx.session.messages
        )
        if already_persisted:
            logger.info(
                "%s Skipping duplicate tool_result for toolCallId=%s",
                log_prefix,
                response.toolCallId,
            )
            # Return None so the caller's ``if dispatched is not None: yield``
            # short-circuits — the duplicate event stays off the SSE stream
            # (so the frontend doesn't render a second widget) and the
            # mid-turn follow-up persist doesn't double-fire (its guard is
            # ``dispatched is not None``).
            return None
        content = (
            response.output
            if isinstance(response.output, str)
            else json.dumps(response.output, ensure_ascii=False)
        )
        ctx.session.messages.append(
            ChatMessage(
                role="tool",
                content=content,
                tool_call_id=response.toolCallId,
            )
        )
        if not entries_replaced:
            state.transcript_builder.append_tool_result(
                tool_use_id=response.toolCallId,
                content=content,
            )
        acc.has_tool_results = True

    elif isinstance(response, StreamFinish):
        acc.stream_completed = True

    return response