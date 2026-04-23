def read_compacted_entries(transcript_path: str) -> list[dict] | None:
    """Read compacted entries from the CLI session file after compaction.

    Parses the JSONL file line-by-line, finds the ``isCompactSummary: true``
    entry, and returns it plus all entries after it.

    The CLI writes the compaction summary BEFORE sending the next message,
    so the file is guaranteed to be flushed by the time we read it.

    Returns a list of parsed dicts, or ``None`` if the file cannot be read
    or no compaction summary is found.
    """
    if not transcript_path:
        return None

    _pbase = projects_base()
    real_path = os.path.realpath(transcript_path)
    if not real_path.startswith(_pbase + os.sep):
        logger.warning(
            "[Transcript] transcript_path outside projects base: %s", transcript_path
        )
        return None

    try:
        content = Path(real_path).read_text()
    except OSError as e:
        logger.warning(
            "[Transcript] Failed to read session file %s: %s", transcript_path, e
        )
        return None

    lines = content.strip().split("\n")
    compact_idx: int | None = None

    for idx, line in enumerate(lines):
        if not line.strip():
            continue
        entry = json.loads(line, fallback=None)
        if not isinstance(entry, dict):
            continue
        if entry.get("isCompactSummary"):
            compact_idx = idx  # don't break — find the LAST summary

    if compact_idx is None:
        logger.debug("[Transcript] No compaction summary found in %s", transcript_path)
        return None

    entries: list[dict] = []
    for line in lines[compact_idx:]:
        if not line.strip():
            continue
        entry = json.loads(line, fallback=None)
        if isinstance(entry, dict):
            entries.append(entry)

    logger.info(
        "[Transcript] Read %d compacted entries from %s (summary at line %d)",
        len(entries),
        transcript_path,
        compact_idx + 1,
    )
    return entries