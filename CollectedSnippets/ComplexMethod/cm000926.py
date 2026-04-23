def _gen_ids_from_jsonl(path: Path) -> set[str]:
    """Extract ``gen-`` message IDs from every assistant entry in a
    Claude CLI JSONL file.

    Tolerant of malformed lines: single bad JSON object doesn't block
    the whole file.  Also reads ``redacted_thinking`` / ``thinking``
    entries that share an ID with their parent (via ``jq -u`` in the
    CLI) and dedups by caller.
    """
    ids: set[str] = set()
    try:
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                entry = json.loads(line, fallback=None)
                if not isinstance(entry, dict):
                    continue
                if entry.get("type") != "assistant":
                    continue
                message = entry.get("message")
                if not isinstance(message, dict):
                    continue
                msg_id = message.get("id")
                if isinstance(msg_id, str) and msg_id.startswith("gen-"):
                    ids.add(msg_id)
    except (OSError, UnicodeDecodeError) as exc:
        logger.debug(
            "Failed to scan JSONL for gen-IDs: path=%s err=%s",
            path,
            exc,
        )
    return ids