def _flatten_assistant_content(blocks: list) -> str:
    """Flatten assistant content blocks into a single plain-text string.

    Structured ``tool_use`` blocks are converted to ``[tool_use: name]``
    placeholders.  ``thinking`` and ``redacted_thinking`` blocks are
    silently dropped — they carry no useful context for compression
    summaries and must not leak into compacted transcripts (the Anthropic
    API requires thinking blocks in the last assistant message to be
    value-identical to the original response; including stale thinking
    text would violate that constraint).

    This is intentional: ``compress_context`` requires plain text for
    token counting and LLM summarization.  The structural loss is
    acceptable because compaction only runs when the original transcript
    was already too large for the model.
    """
    parts: list[str] = []
    for block in blocks:
        if isinstance(block, dict):
            btype = block.get("type", "")
            if btype in _THINKING_BLOCK_TYPES:
                continue
            if btype == "text":
                parts.append(block.get("text", ""))
            elif btype == "tool_use":
                # Drop tool_use entirely — any text representation gets
                # mimicked by the model as plain text instead of actual
                # structured tool calls. The tool results (in the
                # following user/tool_result entry) provide sufficient
                # context about what happened.
                continue
            else:
                continue
        elif isinstance(block, str):
            parts.append(block)
    return "\n".join(parts) if parts else ""