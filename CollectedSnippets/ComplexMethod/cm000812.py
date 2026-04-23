def strip_for_upload(content: str) -> str:
    """Combined single-parse strip of progress entries and stale thinking blocks.

    Equivalent to ``strip_stale_thinking_blocks(strip_progress_entries(content))``
    but parses the JSONL only once, avoiding redundant ``split`` + ``json.loads``
    passes on every upload.
    """
    lines = content.strip().split("\n")
    if not lines:
        return content

    parsed: list[tuple[str, dict | None]] = []
    for line in lines:
        parsed.append((line, json.loads(line, fallback=None)))

    # --- Phase 1: progress stripping (reparent children) ---
    stripped_uuids: set[str] = set()
    uuid_to_parent: dict[str, str] = {}

    for _line, entry in parsed:
        if not isinstance(entry, dict):
            continue
        uid = entry.get("uuid", "")
        parent = entry.get("parentUuid", "")
        if uid:
            uuid_to_parent[uid] = parent
        if (
            entry.get("type", "") in STRIPPABLE_TYPES
            and uid
            and not entry.get("isCompactSummary")
        ):
            stripped_uuids.add(uid)

    reparented: set[str] = set()
    for _line, entry in parsed:
        if not isinstance(entry, dict):
            continue
        parent = entry.get("parentUuid", "")
        original_parent = parent
        seen_parents: set[str] = set()
        while parent in stripped_uuids and parent not in seen_parents:
            seen_parents.add(parent)
            parent = uuid_to_parent.get(parent, "")
        if parent != original_parent:
            entry["parentUuid"] = parent
            uid = entry.get("uuid", "")
            if uid:
                reparented.add(uid)

    # --- Phase 2: identify last assistant for thinking-block stripping ---
    last_asst_msg_id: str | None = None
    last_asst_idx: int | None = None
    for i in range(len(parsed) - 1, -1, -1):
        _line, entry = parsed[i]
        if not isinstance(entry, dict):
            continue
        if entry.get("type", "") in STRIPPABLE_TYPES and not entry.get(
            "isCompactSummary"
        ):
            continue
        msg = entry.get("message", {})
        if msg.get("role") == "assistant":
            last_asst_msg_id = msg.get("id")
            last_asst_idx = i
            break

    # --- Phase 3: single output pass ---
    result_lines: list[str] = []
    thinking_stripped = 0
    for i, (line, entry) in enumerate(parsed):
        if not isinstance(entry, dict):
            result_lines.append(line)
            continue

        # Drop progress/metadata entries
        if entry.get("type", "") in STRIPPABLE_TYPES and not entry.get(
            "isCompactSummary"
        ):
            continue

        needs_reserialize = False
        uid = entry.get("uuid", "")

        # Reparented entries need re-serialization
        if uid in reparented:
            needs_reserialize = True

        # Strip stale thinking blocks from non-last assistant entries.
        # Also strip *signature-less* thinking blocks from the last entry —
        # those come from non-Anthropic providers (e.g. Kimi K2.6 via
        # OpenRouter) and are rejected with ``Invalid `signature` in
        # `thinking` block`` if a subsequent turn is dispatched to an
        # Anthropic model that re-validates them.  Anthropic-emitted
        # thinking blocks always carry a non-empty ``signature`` field, so
        # this filter is a no-op on Sonnet/Opus turns and only kicks in
        # when the prior turn ran on a non-Anthropic vendor.
        if last_asst_idx is not None:
            msg = entry.get("message", {})
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
                    thinking_stripped += len(content_blocks) - len(filtered)
                    entry = {**entry, "message": {**msg, "content": filtered}}
                    needs_reserialize = True

        if needs_reserialize:
            result_lines.append(json.dumps(entry, separators=(",", ":")))
        else:
            result_lines.append(line)

    if thinking_stripped:
        logger.info(
            "[Transcript] Stripped %d stale thinking block(s) from non-last entries",
            thinking_stripped,
        )

    return "\n".join(result_lines) + "\n"