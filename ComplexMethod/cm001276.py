async def reset_copilot_usage(
    user_id: Annotated[str, Security(auth.get_user_id)],
) -> RateLimitResetResponse:
    """Reset the daily CoPilot rate limit by spending credits.

    Allows users who have hit their daily cost limit to spend credits
    to reset their daily usage counter and continue working.
    Returns 400 if the feature is disabled or the user is not over the limit.
    Returns 402 if the user has insufficient credits.
    """
    cost = config.rate_limit_reset_cost
    if cost <= 0:
        raise HTTPException(
            status_code=400,
            detail="Rate limit reset is not available.",
        )

    if not settings.config.enable_credit:
        raise HTTPException(
            status_code=400,
            detail="Rate limit reset is not available (credit system is disabled).",
        )

    daily_limit, weekly_limit, tier = await get_global_rate_limits(
        user_id,
        config.daily_cost_limit_microdollars,
        config.weekly_cost_limit_microdollars,
    )

    if daily_limit <= 0:
        raise HTTPException(
            status_code=400,
            detail="No daily limit is configured — nothing to reset.",
        )

    # Check max daily resets.  get_daily_reset_count returns None when Redis
    # is unavailable; reject the reset in that case to prevent unlimited
    # free resets when the counter store is down.
    reset_count = await get_daily_reset_count(user_id)
    if reset_count is None:
        raise HTTPException(
            status_code=503,
            detail="Unable to verify reset eligibility — please try again later.",
        )
    if config.max_daily_resets > 0 and reset_count >= config.max_daily_resets:
        raise HTTPException(
            status_code=429,
            detail=f"You've used all {config.max_daily_resets} resets for today.",
        )

    # Acquire a per-user lock to prevent TOCTOU races (concurrent resets).
    if not await acquire_reset_lock(user_id):
        raise HTTPException(
            status_code=429,
            detail="A reset is already in progress. Please try again.",
        )

    try:
        # Verify the user is actually at or over their daily limit.
        # (rate_limit_reset_cost intentionally omitted — this object is only
        # used for limit checks, not returned to the client.)
        usage_status = await get_usage_status(
            user_id=user_id,
            daily_cost_limit=daily_limit,
            weekly_cost_limit=weekly_limit,
            tier=tier,
        )
        if daily_limit > 0 and usage_status.daily.used < daily_limit:
            raise HTTPException(
                status_code=400,
                detail="You have not reached your daily limit yet.",
            )

        # If the weekly limit is also exhausted, resetting the daily counter
        # won't help — the user would still be blocked by the weekly limit.
        if weekly_limit > 0 and usage_status.weekly.used >= weekly_limit:
            raise HTTPException(
                status_code=400,
                detail="Your weekly limit is also reached. Resetting the daily limit won't help.",
            )

        # Charge credits.
        credit_model = await get_user_credit_model(user_id)
        try:
            remaining = await credit_model.spend_credits(
                user_id=user_id,
                cost=cost,
                metadata=UsageTransactionMetadata(
                    reason="CoPilot daily rate limit reset",
                ),
            )
        except InsufficientBalanceError as e:
            raise HTTPException(
                status_code=402,
                detail="Insufficient credits to reset your rate limit.",
            ) from e

        # Reset daily usage in Redis.  If this fails, refund the credits
        # so the user is not charged for a service they did not receive.
        if not await reset_daily_usage(user_id, daily_cost_limit=daily_limit):
            # Compensate: refund the charged credits.
            refunded = False
            try:
                await credit_model.top_up_credits(user_id, cost)
                refunded = True
                logger.warning(
                    "Refunded %d credits to user %s after Redis reset failure",
                    cost,
                    user_id[:8],
                )
            except Exception:
                logger.error(
                    "CRITICAL: Failed to refund %d credits to user %s "
                    "after Redis reset failure — manual intervention required",
                    cost,
                    user_id[:8],
                    exc_info=True,
                )
            if refunded:
                raise HTTPException(
                    status_code=503,
                    detail="Rate limit reset failed — please try again later. "
                    "Your credits have not been charged.",
                )
            raise HTTPException(
                status_code=503,
                detail="Rate limit reset failed and the automatic refund "
                "also failed. Please contact support for assistance.",
            )

        # Track the reset count for daily cap enforcement.
        await increment_daily_reset_count(user_id)
    finally:
        await release_reset_lock(user_id)

    # Return updated usage status (public schema — percentages only).
    updated_usage = await get_usage_status(
        user_id=user_id,
        daily_cost_limit=daily_limit,
        weekly_cost_limit=weekly_limit,
        rate_limit_reset_cost=config.rate_limit_reset_cost,
        tier=tier,
    )

    return RateLimitResetResponse(
        success=True,
        credits_charged=cost,
        remaining_balance=remaining,
        usage=CoPilotUsagePublic.from_status(updated_usage),
    )