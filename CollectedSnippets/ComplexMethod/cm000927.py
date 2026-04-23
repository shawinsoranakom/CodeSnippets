def _discover_turn_subagent_gen_ids(
    project_dir: Path,
    session_id: str,
    turn_start_ts: float,
    known: list[str],
) -> list[str]:
    """Gen-IDs from this session's subagents created during this turn.

    Main-turn LLM rounds (incl. fallback retries) arrive on the live
    stream as ``AssistantMessage`` and land on ``known`` via
    ``message_id``.  What's NOT on ``known`` is the CLI's subagent LLM
    calls — chiefly auto-compaction, which spawns a fresh JSONL under
    ``<project_dir>/<session_id>/subagents/agent-acompact-*.jsonl``
    whose gen-IDs never touch our main adapter.  OpenRouter bills them
    anyway, so without this sweep compaction turns under-report cost.

    Scoping: ONLY the current session's subagent dir
    (``<project_dir>/<session_id>/subagents/agent-*.jsonl``) and ONLY
    files whose ``mtime >= turn_start_ts``.  Without both guards we'd
    merge prior turns' gen-IDs (main JSONL accumulates forever) and
    foreign sessions' gen-IDs (the project dir contains every session
    for this cwd), double-billing the user.

    Also covers non-compaction subagents (Task tool etc.) when the CLI
    spawns them — their live-stream visibility depends on SDK version,
    so the sweep is a safety net.  The dedup against ``known`` means
    anything already captured live doesn't double count.

    Preserves ``known`` ordering so main-turn IDs stay first; only
    appends truly new IDs from the sweep.
    """
    merged: list[str] = list(known)
    seen = set(merged)
    subagents_dir = project_dir / session_id / "subagents"
    if not subagents_dir.exists():
        return merged
    try:
        for jsonl in subagents_dir.glob("agent-*.jsonl"):
            try:
                if jsonl.stat().st_mtime < turn_start_ts:
                    continue
            except OSError:
                continue
            for gen_id in _gen_ids_from_jsonl(jsonl):
                if gen_id not in seen:
                    seen.add(gen_id)
                    merged.append(gen_id)
    except OSError as exc:
        logger.debug("Failed to walk subagents dir=%s: %s", subagents_dir, exc)
    return merged