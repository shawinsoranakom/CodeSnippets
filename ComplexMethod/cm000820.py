def _transcript_to_messages(content: str) -> list[dict]:
    """Convert JSONL transcript entries to plain message dicts for compression.

    Parses each line of the JSONL *content*, skips strippable metadata entries
    (progress, file-history-snapshot, etc.), and extracts the ``role`` and
    flattened ``content`` from the ``message`` field of each remaining entry.

    Structured content blocks (``tool_use``, ``tool_result``, images) are
    flattened to plain text via ``_flatten_assistant_content`` and
    ``_flatten_tool_result_content`` so that ``compress_context`` can
    perform token counting and LLM summarization on uniform strings.

    Returns:
        A list of ``{"role": str, "content": str}`` dicts suitable for
        ``compress_context``.
    """
    messages: list[dict] = []
    for line in content.strip().split("\n"):
        if not line.strip():
            continue
        entry = json.loads(line, fallback=None)
        if not isinstance(entry, dict):
            continue
        if entry.get("type", "") in STRIPPABLE_TYPES and not entry.get(
            "isCompactSummary"
        ):
            continue
        msg = entry.get("message", {})
        role = msg.get("role", "")
        if not role:
            continue
        msg_dict: dict = {"role": role}
        raw_content = msg.get("content")
        if role == "assistant" and isinstance(raw_content, list):
            msg_dict["content"] = _flatten_assistant_content(raw_content)
        elif isinstance(raw_content, list):
            msg_dict["content"] = _flatten_tool_result_content(raw_content)
        else:
            msg_dict["content"] = raw_content or ""
        messages.append(msg_dict)
    return messages