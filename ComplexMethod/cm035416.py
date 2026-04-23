def get_token_usage_for_event(event: Event, metrics: Metrics) -> TokenUsage | None:
    """Returns at most one token usage record for either:
      - `tool_call_metadata.model_response.id`, if possible
      - otherwise event.response_id, if set

    If neither exist or none matches in metrics.token_usages, returns None.
    """
    # 1) Use the tool_call_metadata's response.id if present
    if event.tool_call_metadata and event.tool_call_metadata.model_response:
        tool_response_id = event.tool_call_metadata.model_response.get('id')
        if tool_response_id:
            usage_rec = next(
                (u for u in metrics.token_usages if u.response_id == tool_response_id),
                None,
            )
            if usage_rec is not None:
                return usage_rec

    # 2) Fallback to the top-level event.response_id if present
    if event.response_id:
        return next(
            (u for u in metrics.token_usages if u.response_id == event.response_id),
            None,
        )

    return None