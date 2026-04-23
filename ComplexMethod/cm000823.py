def _rechain_tail(compressed_prefix: str, tail_lines: list[str]) -> str:
    """Patch tail entries so their parentUuid chain links to the compressed prefix.

    The first tail entry's ``parentUuid`` is set to the ``uuid`` of the
    last entry in the compressed prefix.  Subsequent tail entries are
    rechained to point to their predecessor in the tail — their original
    ``parentUuid`` values may reference entries that were compressed away.
    """
    if not tail_lines:
        return ""
    # Find the last uuid in the compressed prefix
    last_prefix_uuid = ""
    for line in reversed(compressed_prefix.strip().split("\n")):
        if not line.strip():
            continue
        entry = json.loads(line, fallback=None)
        if isinstance(entry, dict) and "uuid" in entry:
            last_prefix_uuid = entry["uuid"]
            break

    result_lines: list[str] = []
    prev_uuid: str | None = None
    for i, line in enumerate(tail_lines):
        entry = json.loads(line, fallback=None)
        if not isinstance(entry, dict):
            # Safety guard: _find_last_assistant_entry already filters empty
            # lines, and well-formed JSONL always parses to dicts.  Non-dict
            # lines are passed through unchanged; prev_uuid is intentionally
            # NOT updated so the next dict entry chains to the last known uuid.
            result_lines.append(line)
            continue
        if i == 0:
            entry["parentUuid"] = last_prefix_uuid
        elif prev_uuid is not None:
            entry["parentUuid"] = prev_uuid
        prev_uuid = entry.get("uuid")
        result_lines.append(json.dumps(entry, separators=(",", ":")))
    return "\n".join(result_lines) + "\n"