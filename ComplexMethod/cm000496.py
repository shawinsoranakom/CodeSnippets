async def modify_stripe_subscription_for_tier(
    user_id: str, tier: SubscriptionTier
) -> bool:
    """Change a Stripe subscription to a new paid tier.

    Upgrades (e.g. PRO→BUSINESS) apply immediately via ``stripe.Subscription.modify``
    with ``proration_behavior="create_prorations"``: Stripe credits unused time on
    the old plan and charges the pro-rated amount for the new plan in the same
    billing cycle.

    Downgrades (e.g. BUSINESS→PRO) are deferred to the end of the current billing
    period via a Stripe Subscription Schedule: the user keeps their current tier
    for the time they already paid for, and the new tier takes effect when the
    next invoice is generated. The DB tier flip happens via the webhook fired
    when the schedule advances to its next phase.

    Returns:
        True  — a subscription was found and modified/scheduled successfully.
        False — no active/trialing subscription exists (e.g. admin-granted tier or
                first-time paid signup); caller should fall back to Checkout.

    Raises stripe.StripeError on API failures so callers can propagate a 502.
    Raises ValueError when no Stripe price ID is configured for the tier.
    """
    price_id = await get_subscription_price_id(tier)
    if not price_id:
        raise ValueError(f"No Stripe price ID configured for tier {tier}")

    user = await get_user_by_id(user_id)
    if not user.stripe_customer_id:
        return False
    current_tier = user.subscription_tier or SubscriptionTier.FREE

    sub = await _get_active_subscription(user.stripe_customer_id)
    if sub is None:
        return False
    items = sub["items"].data
    if not items:
        return False
    sub_id = sub.id

    # Invalidate the cache unconditionally on exit (success OR failure): any
    # Stripe mutation below — clearing cancel_at_period_end, releasing an old
    # schedule, creating a new one — may have landed partially before an error
    # was raised, and the cached pending-change state would otherwise go stale
    # for up to 30s until the TTL expires.
    try:
        if is_tier_downgrade(current_tier, tier):
            await _schedule_downgrade_at_period_end(sub, price_id, user_id, tier)
            return True

        # Upgrade path. If a schedule is attached from a previous pending
        # downgrade, release it first — an upgrade expresses the user's
        # intent to be on this tier immediately, which overrides any pending
        # deferred change. Ignore terminal-state errors from release.
        if sub.schedule:
            existing_schedule_id = (
                sub.schedule if isinstance(sub.schedule, str) else sub.schedule.id
            )
            await _release_schedule_ignoring_terminal(
                existing_schedule_id, "modify_stripe_subscription_for_tier"
            )

        # If a paid→FREE cancel is pending (cancel_at_period_end=True), clear it
        # as part of the upgrade — the user is explicitly choosing to stay on a
        # paid tier. Without this, the sub would be upgraded AND still cancelled
        # at period end, leaving a confusing dual state.
        modify_kwargs: dict = {
            "items": [{"id": items[0].id, "price": price_id}],
            "proration_behavior": "create_prorations",
        }
        if sub.cancel_at_period_end:
            modify_kwargs["cancel_at_period_end"] = False

        await stripe.Subscription.modify_async(sub_id, **modify_kwargs)
        # Flip the DB tier immediately. The customer.subscription.updated webhook
        # will also fire and set it again — idempotent. Without this synchronous
        # update, the UI refetches before the webhook lands and shows the old
        # tier, making the upgrade look like a no-op to the user.
        #
        # Swallow DB-write exceptions here: Stripe is authoritative and the
        # modify above already succeeded (the user has been charged). If the
        # DB write fails and we re-raised, the API would return 5xx and the UI
        # would surface a failed upgrade to a user who was already charged.
        # The customer.subscription.updated webhook will reconcile the DB shortly.
        #
        # Only catch actual DB/connection failures — letting KeyError,
        # AttributeError etc. propagate so programming errors surface in Sentry
        # instead of being silently masked as benign DB-write-swallow events.
        try:
            await set_subscription_tier(user_id, tier)
        except (PrismaError, ConnectionError, asyncio.TimeoutError):
            logger.exception(
                "modify_stripe_subscription_for_tier: Stripe modify on sub %s"
                " succeeded for user %s → %s but DB tier flip failed; webhook"
                " will reconcile",
                sub_id,
                user_id,
                tier,
            )
        logger.info(
            "modify_stripe_subscription_for_tier: upgraded sub %s for user %s → %s",
            sub_id,
            user_id,
            tier,
        )
        return True
    finally:
        get_pending_subscription_change.cache_delete(user_id)