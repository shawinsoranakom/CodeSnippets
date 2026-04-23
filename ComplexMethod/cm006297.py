def _extract_trace_io(records: list[_SpanIORecord]) -> TraceIO:
    """Core I/O heuristic operating on normalised :class:`_SpanIORecord` objects.

    **Input heuristic** — searches for the first record whose name contains
    :data:`_CHAT_INPUT_SPAN_NAME` (``"Chat Input"``).  The ``input_value`` key
    from that record's ``inputs`` dict is surfaced as the trace-level input.

    **Output heuristic** — collects all *root* records (``parent_span_id`` is
    ``None``) that have already finished (``end_time`` is not ``None``), then
    picks the one with the latest ``end_time``.  Its full ``outputs`` dict is
    surfaced as the trace-level output.

    Args:
        records: Normalised span records for a single trace.

    Returns:
        Dict with ``"input"`` and ``"output"`` keys.
    """
    chat_input = next((r for r in records if _CHAT_INPUT_SPAN_NAME in (r.name or "")), None)
    input_value = None
    if chat_input and chat_input.inputs:
        input_value = chat_input.inputs.get("input_value")

    root_records = [r for r in records if r.parent_span_id is None and r.end_time]
    output_value = None
    if root_records:
        root_records_sorted = sorted(
            root_records,
            key=lambda r: r.end_time or _UTC_MIN,
            reverse=True,
        )
        if root_records_sorted[0].outputs:
            output_value = root_records_sorted[0].outputs

    return {
        "input": {"input_value": input_value} if input_value else None,
        "output": output_value,
    }