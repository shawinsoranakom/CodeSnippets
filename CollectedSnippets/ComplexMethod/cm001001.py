def response_from_outcome(
    *,
    outcome: SessionOutcome,
    result: SessionResult,
    inner_session_id: str,
    parent_session_id: str | None,
    elapsed: float,
) -> SubSessionStatusResponse:
    """Translate a ``(SessionOutcome, SessionResult)`` tuple into the
    ``SubSessionStatusResponse`` contract the LLM sees.

    ``completed`` surfaces the aggregated response text + tool calls.
    ``failed`` returns the error marker with the same handles.
    ``running`` returns just the polling handles so the agent can resume.
    ``queued`` means the target session already had a turn in flight; the
    message was appended to its pending buffer and will be processed by
    the existing turn on its next drain.
    """
    link = _sub_session_link(inner_session_id)
    if outcome == "queued":
        return SubSessionStatusResponse(
            message=(
                f"Target session already had a turn in flight; the message "
                f"was queued ({result.pending_buffer_length} now pending) and "
                "will be processed by the existing turn on its next drain. "
                f"Call get_sub_session_result to poll progress"
                f"{f' or watch live at {link}' if link else ''}."
            ),
            session_id=parent_session_id,
            status="queued",
            sub_session_id=inner_session_id,
            sub_autopilot_session_id=inner_session_id,
            sub_autopilot_session_link=link,
            elapsed_seconds=round(elapsed, 2),
        )

    if outcome == "running":
        return SubSessionStatusResponse(
            message=(
                f"Sub-AutoPilot is still running after {elapsed:.0f}s."
                f"{f' Watch live at {link}.' if link else ''} "
                "Call get_sub_session_result (optionally with "
                "include_progress=true) to wait, poll, or inspect progress."
            ),
            session_id=parent_session_id,
            status="running",
            sub_session_id=inner_session_id,
            sub_autopilot_session_id=inner_session_id,
            sub_autopilot_session_link=link,
            elapsed_seconds=round(elapsed, 2),
        )

    if outcome == "failed":
        return SubSessionStatusResponse(
            message="Sub-AutoPilot failed. See the sub's transcript for details.",
            session_id=parent_session_id,
            status="error",
            sub_session_id=inner_session_id,
            sub_autopilot_session_id=inner_session_id,
            sub_autopilot_session_link=link,
            elapsed_seconds=round(elapsed, 2),
        )

    # completed
    return SubSessionStatusResponse(
        message=f"Sub-AutoPilot completed.{f' View at {link}.' if link else ''}",
        session_id=parent_session_id,
        status="completed",
        sub_session_id=inner_session_id,
        sub_autopilot_session_id=inner_session_id,
        sub_autopilot_session_link=link,
        response=result.response_text,
        tool_calls=[tc.model_dump() for tc in result.tool_calls],
        elapsed_seconds=round(elapsed, 2),
    )