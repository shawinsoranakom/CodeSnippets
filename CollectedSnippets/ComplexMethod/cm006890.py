def _build_result(raw: dict[str, Any]) -> FlowResult:
    """Construct a :class:`FlowResult` from the dict returned by ``run_flow()``."""
    # ``success`` may be absent (treat as True for forward compat)
    is_error = (raw.get("success") is False) or raw.get("type") == "error"
    status = "error" if is_error else "success"

    # Extract primary text from several candidate keys, in priority order
    text: str | None = None
    for key in ("result", "text", "output"):
        val = raw.get(key)
        if val is not None:
            text = val if isinstance(val, str) else json.dumps(val)
            break

    messages: list[dict[str, Any]] = raw.get("messages") or []
    if not isinstance(messages, list):
        messages = []

    outputs: dict[str, Any] = raw.get("outputs") or raw.get("result_dict") or {}
    if not isinstance(outputs, dict):
        outputs = {}

    error_msg: str | None = None
    if is_error:
        error_msg = raw.get("exception_message") or raw.get("error") or "Unknown error"

    return FlowResult(
        status=status,
        text=text,
        messages=messages,
        outputs=outputs,
        logs=raw.get("logs", ""),
        error=error_msg,
        timing=raw.get("timing"),
        raw=raw,
    )