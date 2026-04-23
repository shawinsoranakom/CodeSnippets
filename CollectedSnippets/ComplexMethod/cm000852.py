async def check_rate_limit(
    user_id: str,
    daily_cost_limit: int,
    weekly_cost_limit: int,
) -> None:
    """Check if user is within rate limits. Raises RateLimitExceeded if not.

    This is a pre-turn soft check. The authoritative usage counter is updated
    by ``record_cost_usage()`` after the turn completes. Under concurrency,
    two parallel turns may both pass this check against the same snapshot.
    This is acceptable because cost-based limits are approximate by nature
    (the exact cost is unknown until after generation).

    Fails open: if Redis is unavailable, allows the request.
    """
    # Short-circuit: when both limits are 0 (unlimited) skip the Redis
    # round-trip entirely.
    if daily_cost_limit <= 0 and weekly_cost_limit <= 0:
        return

    now = datetime.now(UTC)
    try:
        redis = await get_redis_async()
        daily_raw, weekly_raw = await asyncio.gather(
            redis.get(_daily_key(user_id, now=now)),
            redis.get(_weekly_key(user_id, now=now)),
        )
        daily_used = int(daily_raw or 0)
        weekly_used = int(weekly_raw or 0)
    except (RedisError, ConnectionError, OSError):
        logger.warning("Redis unavailable for rate limit check, allowing request")
        return

    if daily_cost_limit > 0 and daily_used >= daily_cost_limit:
        raise RateLimitExceeded("daily", _daily_reset_time(now=now))

    if weekly_cost_limit > 0 and weekly_used >= weekly_cost_limit:
        raise RateLimitExceeded("weekly", _weekly_reset_time(now=now))