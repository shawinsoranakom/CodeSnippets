async def get_subscription_status(
    user_id: Annotated[str, Security(get_user_id)],
) -> SubscriptionStatusResponse:
    user = await get_user_by_id(user_id)
    tier = user.subscription_tier or SubscriptionTier.FREE

    paid_tiers = [SubscriptionTier.PRO, SubscriptionTier.BUSINESS]
    price_ids = await asyncio.gather(
        *[get_subscription_price_id(t) for t in paid_tiers]
    )

    tier_costs: dict[str, int] = {
        SubscriptionTier.FREE.value: 0,
        SubscriptionTier.ENTERPRISE.value: 0,
    }

    async def _cost(pid: str | None) -> int:
        return (await _get_stripe_price_amount(pid) or 0) if pid else 0

    costs = await asyncio.gather(*[_cost(pid) for pid in price_ids])
    for t, cost in zip(paid_tiers, costs):
        tier_costs[t.value] = cost

    current_monthly_cost = tier_costs.get(tier.value, 0)
    proration_credit = await get_proration_credit_cents(user_id, current_monthly_cost)

    try:
        pending = await get_pending_subscription_change(user_id)
    except (stripe.StripeError, PendingChangeUnknown):
        # Swallow Stripe-side failures (rate limits, transient network) AND
        # PendingChangeUnknown (LaunchDarkly price-id lookup failed). Both
        # propagate past the cache so the next request retries fresh instead
        # of serving a stale None for the TTL window. Let real bugs (KeyError,
        # AttributeError, etc.) propagate so they surface in Sentry.
        logger.exception(
            "get_subscription_status: failed to resolve pending change for user %s",
            user_id,
        )
        pending = None

    response = SubscriptionStatusResponse(
        tier=tier.value,
        monthly_cost=current_monthly_cost,
        tier_costs=tier_costs,
        proration_credit_cents=proration_credit,
    )
    if pending is not None:
        pending_tier_enum, pending_effective_at = pending
        if pending_tier_enum == SubscriptionTier.FREE:
            response.pending_tier = "FREE"
        elif pending_tier_enum == SubscriptionTier.PRO:
            response.pending_tier = "PRO"
        elif pending_tier_enum == SubscriptionTier.BUSINESS:
            response.pending_tier = "BUSINESS"
        if response.pending_tier is not None:
            response.pending_tier_effective_at = pending_effective_at
    return response