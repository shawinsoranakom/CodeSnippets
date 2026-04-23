async def record_turn_cost_from_openrouter(
    *,
    session: "ChatSession",
    user_id: str | None,
    model: str | None,
    prompt_tokens: int,
    completion_tokens: int,
    cache_read_tokens: int,
    cache_creation_tokens: int,
    generation_ids: list[str],
    cli_project_dir: str | None,
    cli_session_id: str | None,
    turn_start_ts: float | None,
    fallback_cost_usd: float | None,
    api_key: str | None,
    log_prefix: str,
) -> None:
    """Persist turn cost from OpenRouter's authoritative ``/generation``.

    Writes a single cost-analytics row via :func:`persist_and_record_usage`
    — same method used for the Anthropic-direct sync path — so the
    cost-log append and rate-limit counter stay consistent.  No double
    counting: the caller skips its own sync persist for non-Anthropic
    OpenRouter turns and defers entirely to this task.

    Launched via ``asyncio.create_task`` from the stream ``finally`` block
    so the ~500-2000ms ``/generation`` indexing delay doesn't add latency
    to the turn.  During that window the rate-limit counter is briefly
    unaware of the turn's cost; back-to-back turns in that sub-second
    gap see a stale counter.  Acceptable tradeoff — the alternative
    (writing a possibly-wrong estimate synchronously) creates a
    double-count when the reconcile delta arrives.

    Fallback semantics: if every generation lookup fails, records
    ``fallback_cost_usd`` instead so the rate-limit counter isn't left
    completely empty.  Keeps behaviour at-worst equivalent to the
    rate-card estimate that came before this task existed.
    """
    if not api_key:
        logger.debug(
            "%s OpenRouter cost record skipped: no API key available",
            log_prefix,
        )
        return

    # Merge in any gen-IDs from CLI subagent JSONLs the live stream
    # didn't surface — chiefly SDK-internal compaction, which spawns a
    # summarisation LLM call under
    # ``<project_dir>/<cli_session_id>/subagents/...`` that OpenRouter
    # bills but doesn't emit via our main adapter.  Safe no-op when no
    # compaction happened (no subagent files created this turn) or the
    # CLI wrote nothing there.
    #
    # The sweep is SESSION-scoped (``<cli_session_id>/subagents/``, not
    # the whole project dir) and TURN-scoped (mtime >= turn_start_ts).
    # Both guards are load-bearing: the project dir contains every
    # session for this cwd, and subagent files persist across turns,
    # so an unscoped sweep would re-bill prior turns and foreign
    # sessions' gen-IDs.
    if cli_project_dir and cli_session_id and turn_start_ts is not None:
        merged_ids = _discover_turn_subagent_gen_ids(
            Path(os.path.expanduser(cli_project_dir)),
            cli_session_id,
            turn_start_ts,
            generation_ids,
        )
        if len(merged_ids) != len(generation_ids):
            logger.info(
                "%s[cost-record] discovered %d additional gen-IDs in "
                "session subagents (compaction / Task) — reconcile "
                "covers all",
                log_prefix,
                len(merged_ids) - len(generation_ids),
            )
        generation_ids = merged_ids

    if not generation_ids:
        return

    try:
        async with httpx.AsyncClient() as client:
            tasks = [
                _fetch_generation_cost(client, gen_id, api_key, log_prefix)
                for gen_id in generation_ids
            ]
            results = await asyncio.gather(*tasks, return_exceptions=False)
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "%s OpenRouter cost record failed to fetch any generation "
            "(falling back to rate-card estimate): %s",
            log_prefix,
            exc,
        )
        results = []

    fetched = [r for r in results if isinstance(r, (int, float))]
    if fetched and len(fetched) == len(generation_ids):
        real_cost: float | None = sum(fetched)
        # Log real (OpenRouter billed) vs CLI rate-card estimate so an
        # operator can spot divergence without querying OpenRouter by
        # hand.  Under-count typically means a gen-ID source we don't
        # capture live (e.g. title model, background LLM calls running
        # outside the main stream); over-count means the CLI's rate
        # table is stale vs. OpenRouter's current pricing.
        delta_pct: float | None = None
        if fallback_cost_usd and fallback_cost_usd > 0:
            delta_pct = (real_cost - fallback_cost_usd) / fallback_cost_usd * 100
        logger.info(
            "%s[cost-record] OpenRouter real=$%.6f cli_estimate=$%s "
            "delta=%s (gen_ids=%d)",
            log_prefix,
            real_cost,
            f"{fallback_cost_usd:.6f}" if fallback_cost_usd is not None else "?",
            f"{delta_pct:+.1f}%" if delta_pct is not None else "n/a",
            len(generation_ids),
        )
    else:
        real_cost = fallback_cost_usd
        if fetched:
            # Partial success: some lookups returned a cost, others didn't.
            # Trusting the partial sum would under-report; fall back to the
            # estimate so rate-limit enforcement stays conservative.
            logger.warning(
                "%s[cost-record] OpenRouter partial lookup (%d/%d) — "
                "using fallback estimate=$%s",
                log_prefix,
                len(fetched),
                len(generation_ids),
                real_cost,
            )
        else:
            logger.warning(
                "%s[cost-record] OpenRouter lookup failed for all gens — "
                "using fallback estimate=$%s",
                log_prefix,
                real_cost,
            )

    try:
        await persist_and_record_usage(
            session=session,
            user_id=user_id,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cache_read_tokens=cache_read_tokens,
            cache_creation_tokens=cache_creation_tokens,
            log_prefix=f"{log_prefix}[cost-record]",
            cost_usd=real_cost,
            model=model,
            provider="open_router",
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "%s[cost-record] failed to persist: %s",
            log_prefix,
            exc,
        )