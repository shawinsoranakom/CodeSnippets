def strip_stale_thinking_blocks(content: str) -> str:
    """Remove thinking/redacted_thinking blocks from non-last assistant entries.

    The Anthropic API only requires thinking blocks in the **last** assistant
    message to be value-identical to the original response.  Older assistant
    entries carry stale thinking blocks that consume significant tokens
    (often 10-50K each) without providing useful context for ``--resume``.

    Stripping them before upload prevents the CLI from triggering compaction
    every turn just to compress away the stale thinking bloat.
    """
    lines = content.strip().split("\n")
    if not lines:
        return content

    parsed: list[tuple[str, dict | None]] = []
    for line in lines:
        parsed.append((line, json.loads(line, fallback=None)))

    # Reverse scan to find the last assistant message ID and index.
    last_asst_msg_id: str | None = None
    last_asst_idx: int | None = None
    for i in range(len(parsed) - 1, -1, -1):
        _line, entry = parsed[i]
        if not isinstance(entry, dict):
            continue
        msg = entry.get("message", {})
        if msg.get("role") == "assistant":
            last_asst_msg_id = msg.get("id")
            last_asst_idx = i
            break

    if last_asst_idx is None:
        return content

    result_lines: list[str] = []
    stripped_count = 0
    for i, (line, entry) in enumerate(parsed):
        if not isinstance(entry, dict):
            result_lines.append(line)
            continue

        msg = entry.get("message", {})
        # Only strip from assistant entries that are NOT the last turn.
        # Use msg_id matching when available; fall back to index for entries
        # without an id field.
        is_last_turn = (
            last_asst_msg_id is not None and msg.get("id") == last_asst_msg_id
        ) or (last_asst_msg_id is None and i == last_asst_idx)
        if msg.get("role") == "assistant" and isinstance(msg.get("content"), list):
            content_blocks = msg["content"]
            producing_model = msg.get("model") if isinstance(msg, dict) else None
            filtered = [
                b
                for b in content_blocks
                if not _should_strip_thinking_block(
                    b,
                    is_last_turn=is_last_turn,
                    producing_model=producing_model,
                )
            ]
            if len(filtered) < len(content_blocks):
                stripped_count += len(content_blocks) - len(filtered)
                entry = {**entry, "message": {**msg, "content": filtered}}
                result_lines.append(json.dumps(entry, separators=(",", ":")))
                continue

        result_lines.append(line)

    if stripped_count:
        logger.info(
            "[Transcript] Stripped %d stale thinking block(s) from non-last entries",
            stripped_count,
        )

    return "\n".join(result_lines) + "\n"