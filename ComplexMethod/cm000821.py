def _find_last_assistant_entry(
    content: str,
) -> tuple[list[str], list[str]]:
    """Split JSONL lines into (compressible_prefix, preserved_tail).

    The tail starts at the **first** entry of the last assistant turn and
    includes everything after it (typically trailing user messages).  An
    assistant turn can span multiple consecutive JSONL entries sharing the
    same ``message.id`` (e.g., a thinking entry followed by a tool_use
    entry).  All entries of the turn are preserved verbatim.

    The Anthropic API requires that ``thinking`` and ``redacted_thinking``
    blocks in the **last** assistant message remain value-identical to the
    original response (the API validates parsed signature values, not raw
    JSON bytes).  By excluding the entire turn from compression we
    guarantee those blocks are never altered.

    Returns ``(all_lines, [])`` when no assistant entry is found.
    """
    lines = [ln for ln in content.strip().split("\n") if ln.strip()]

    # Parse all lines once to avoid double JSON deserialization.
    # json.loads with fallback=None returns Any; non-dict entries are
    # safely skipped by the isinstance(entry, dict) guards below.
    parsed: list = [json.loads(ln, fallback=None) for ln in lines]

    # Reverse scan: find the message.id and index of the last assistant entry.
    last_asst_msg_id: str | None = None
    last_asst_idx: int | None = None
    for i in range(len(parsed) - 1, -1, -1):
        entry = parsed[i]
        if not isinstance(entry, dict):
            continue
        msg = entry.get("message", {})
        if msg.get("role") == "assistant":
            last_asst_idx = i
            last_asst_msg_id = msg.get("id")
            break

    if last_asst_idx is None:
        return lines, []

    # If the assistant entry has no message.id, fall back to preserving
    # from that single entry onward — safer than compressing everything.
    if last_asst_msg_id is None:
        return lines[:last_asst_idx], lines[last_asst_idx:]

    # Forward scan: find the first entry of this turn (same message.id).
    first_turn_idx: int | None = None
    for i, entry in enumerate(parsed):
        if not isinstance(entry, dict):
            continue
        msg = entry.get("message", {})
        if msg.get("role") == "assistant" and msg.get("id") == last_asst_msg_id:
            first_turn_idx = i
            break

    if first_turn_idx is None:
        return lines, []
    return lines[:first_turn_idx], lines[first_turn_idx:]