def strip_progress_entries(content: str) -> str:
    """Remove progress/metadata entries from a JSONL transcript.

    Removes entries whose ``type`` is in ``STRIPPABLE_TYPES`` and reparents
    any remaining child entries so the ``parentUuid`` chain stays intact.
    Typically reduces transcript size by ~30%.

    Entries that are not stripped or reparented are kept as their original
    raw JSON line to avoid unnecessary re-serialization that changes
    whitespace or key ordering.
    """
    lines = content.strip().split("\n")

    # Parse entries, keeping the original line alongside the parsed dict.
    parsed: list[tuple[str, dict | None]] = []
    for line in lines:
        parsed.append((line, json.loads(line, fallback=None)))

    # First pass: identify stripped UUIDs and build parent map.
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

    # Second pass: keep non-stripped entries, reparenting where needed.
    # Preserve original line when no reparenting is required.
    reparented: set[str] = set()
    for _line, entry in parsed:
        if not isinstance(entry, dict):
            continue
        parent = entry.get("parentUuid", "")
        original_parent = parent
        # seen_parents is local per-entry (not shared across iterations) so
        # it can only detect cycles within a single ancestry walk, not across
        # entries.  This is intentional: each entry's parent chain is
        # independent, and reusing a global set would incorrectly short-circuit
        # valid re-use of the same UUID as a parent in different subtrees.
        seen_parents: set[str] = set()
        while parent in stripped_uuids and parent not in seen_parents:
            seen_parents.add(parent)
            parent = uuid_to_parent.get(parent, "")
        if parent != original_parent:
            entry["parentUuid"] = parent
            uid = entry.get("uuid", "")
            if uid:
                reparented.add(uid)

    result_lines: list[str] = []
    for line, entry in parsed:
        if not isinstance(entry, dict):
            result_lines.append(line)
            continue
        if entry.get("type", "") in STRIPPABLE_TYPES and not entry.get(
            "isCompactSummary"
        ):
            continue
        uid = entry.get("uuid", "")
        if uid in reparented:
            # Re-serialize only entries whose parentUuid was changed.
            result_lines.append(json.dumps(entry, separators=(",", ":")))
        else:
            result_lines.append(line)

    return "\n".join(result_lines) + "\n"