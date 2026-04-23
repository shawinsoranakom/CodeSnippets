async def persist_and_record_usage(
    *,
    session: ChatSession | None,
    user_id: str | None,
    prompt_tokens: int,
    completion_tokens: int,
    cache_read_tokens: int = 0,
    cache_creation_tokens: int = 0,
    log_prefix: str = "",
    cost_usd: float | str | None = None,
    model: str | None = None,
    provider: str = "open_router",
) -> int:
    """Persist token usage to session and record generation cost for rate limiting.

    Rate-limit counters are charged in microdollars against the provider's
    reported cost (``cost_usd``), so cache discounts and cross-model pricing
    differences are already reflected. When cost is unknown the turn is
    logged but the rate-limit counter is left alone — the caller logs an
    error at the point the absence is detected.

    Args:
        session: The chat session to append usage to (may be None on error).
        user_id: User ID for rate-limit counters (skipped if None).
        prompt_tokens: Uncached input tokens.
        completion_tokens: Output tokens.
        cache_read_tokens: Tokens served from prompt cache (Anthropic only).
        cache_creation_tokens: Tokens written to prompt cache (Anthropic only).
        log_prefix: Prefix for log messages (e.g. "[SDK]", "[Baseline]").
        cost_usd: Real generation cost for the turn (float from SDK or parsed
            from OpenRouter usage.cost). ``None`` means the provider did not
            report a cost and rate limiting is skipped for this turn.
        model: Model identifier for cost log attribution.
        provider: Cost provider name (e.g. "anthropic", "open_router").

    Returns:
        The computed total_tokens (prompt + completion; cache excluded).
    """
    prompt_tokens = max(0, prompt_tokens)
    completion_tokens = max(0, completion_tokens)
    cache_read_tokens = max(0, cache_read_tokens)
    cache_creation_tokens = max(0, cache_creation_tokens)

    no_tokens = (
        prompt_tokens <= 0
        and completion_tokens <= 0
        and cache_read_tokens <= 0
        and cache_creation_tokens <= 0
    )
    if no_tokens and cost_usd is None:
        return 0

    # total_tokens = prompt + completion. Cache tokens are tracked
    # separately and excluded from total so both baseline and SDK
    # paths share the same semantics.
    total_tokens = prompt_tokens + completion_tokens

    if session is not None:
        session.usage.append(
            Usage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                cache_read_tokens=cache_read_tokens,
                cache_creation_tokens=cache_creation_tokens,
            )
        )

    if cache_read_tokens or cache_creation_tokens:
        logger.info(
            f"{log_prefix} Turn usage: uncached={prompt_tokens}, cache_read={cache_read_tokens},"
            f" cache_create={cache_creation_tokens}, output={completion_tokens},"
            f" total={total_tokens}, cost_usd={cost_usd}"
        )
    else:
        logger.info(
            f"{log_prefix} Turn usage: prompt={prompt_tokens}, completion={completion_tokens},"
            f" total={total_tokens}, cost_usd={cost_usd}"
        )

    cost_float: float | None = None
    if cost_usd is not None:
        try:
            val = float(cost_usd)
        except (ValueError, TypeError):
            logger.error(
                "%s cost_usd is not numeric: %r — rate limit skipped",
                log_prefix,
                cost_usd,
            )
        else:
            if not math.isfinite(val):
                logger.error(
                    "%s cost_usd is non-finite: %r — rate limit skipped",
                    log_prefix,
                    val,
                )
            elif val < 0:
                logger.warning(
                    "%s cost_usd %s is negative — skipping rate-limit + cost log",
                    log_prefix,
                    val,
                )
            else:
                cost_float = val

    cost_microdollars = usd_to_microdollars(cost_float)

    if user_id and cost_microdollars is not None and cost_microdollars > 0:
        # record_cost_usage() owns its fail-open handling for Redis/network
        # errors. Don't wrap with a broad except here — unexpected accounting
        # bugs should surface instead of being silently logged as warnings.
        await record_cost_usage(
            user_id=user_id,
            cost_microdollars=cost_microdollars,
        )

    # Log to PlatformCostLog for admin cost dashboard.
    # Include entries where cost_usd is set even if token count is 0
    # (e.g. fully-cached Anthropic responses where only cache tokens
    # accumulate a charge without incrementing total_tokens).
    if user_id and (total_tokens > 0 or cost_float is not None):
        session_id = session.session_id if session else None

        if cost_float is not None:
            tracking_type = "cost_usd"
            tracking_amount = cost_float
        else:
            tracking_type = "tokens"
            tracking_amount = total_tokens

        _schedule_cost_log(
            PlatformCostEntry(
                user_id=user_id,
                graph_exec_id=session_id,
                block_id=COPILOT_BLOCK_ID,
                block_name=_copilot_block_name(log_prefix),
                provider=provider,
                credential_id=COPILOT_CREDENTIAL_ID,
                cost_microdollars=cost_microdollars,
                input_tokens=prompt_tokens,
                output_tokens=completion_tokens,
                cache_read_tokens=cache_read_tokens or None,
                cache_creation_tokens=cache_creation_tokens or None,
                model=model,
                tracking_type=tracking_type,
                tracking_amount=tracking_amount,
                metadata={
                    "tracking_type": tracking_type,
                    "tracking_amount": tracking_amount,
                    "cache_read_tokens": cache_read_tokens,
                    "cache_creation_tokens": cache_creation_tokens,
                    "source": "copilot",
                },
            )
        )

    return total_tokens