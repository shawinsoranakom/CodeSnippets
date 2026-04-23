async def get_pending_subscription_change(
    user_id: str,
) -> tuple[SubscriptionTier, datetime] | None:
    """Return ``(pending_tier, effective_at)`` when a change is queued, else ``None``.

    Reflects both Subscription Schedule phase transitions (paid→paid downgrade)
    and ``cancel_at_period_end=True`` (paid→FREE cancel).

    Cached for 30 seconds per user_id. *Why the cache exists:* this function
    runs on every dashboard/home fetch and would otherwise fire
    2× Subscription.list + 1× Schedule.retrieve per page load. A busy user
    polling the billing page would quickly brush up against Stripe's per-API
    rate limits; the 30s TTL absorbs dashboard polling while being short
    enough that the UI reconciles quickly after a downgrade / cancel action.

    *Invalidation contract.* Every call-site that mutates Stripe state which
    could change the pending-change answer MUST call
    ``get_pending_subscription_change.cache_delete(user_id)`` so the UI never
    shows a stale pending badge after a user-visible action. Current
    invalidators (keep this list in sync when adding new mutators):

    - ``set_subscription_tier`` — admin or webhook-driven tier flip.
    - ``modify_stripe_subscription_for_tier`` — ``finally`` block (covers
      upgrade path clear + downgrade-schedule create + any partial failure).
    - ``release_pending_subscription_schedule`` — ``finally`` block when a
      schedule release OR ``cancel_at_period_end`` clear succeeded.
    - ``cancel_stripe_subscription`` — after scheduling period-end cancel.
    - ``sync_subscription_from_stripe`` — webhook entry point.
    - ``set_user_tier`` (``backend.copilot.rate_limit``) — admin tier override
      invalidates any cached pending state keyed off the old tier.
    """
    user = await get_user_by_id(user_id)
    if not user.stripe_customer_id:
        # Short-circuit for users with no Stripe customer (admin-granted tiers,
        # FREE-only users): skip the Stripe API calls entirely.
        return None

    pro_price, biz_price = await asyncio.gather(
        get_subscription_price_id(SubscriptionTier.PRO),
        get_subscription_price_id(SubscriptionTier.BUSINESS),
    )
    price_to_tier: dict[str, SubscriptionTier] = {}
    if pro_price:
        price_to_tier[pro_price] = SubscriptionTier.PRO
    if biz_price:
        price_to_tier[biz_price] = SubscriptionTier.BUSINESS
    if not price_to_tier:
        logger.warning(
            "get_pending_subscription_change: no Stripe price IDs resolvable for"
            " PRO/BUSINESS (LaunchDarkly fetch failed?); raising to bypass the"
            " None cache so the next request retries fresh"
        )
        raise PendingChangeUnknown(
            "Stripe price lookup failed; pending-change state cannot be determined"
        )

    sub = await _get_active_subscription(user.stripe_customer_id)
    if sub is None:
        return None
    period_end = sub.current_period_end
    if not isinstance(period_end, int):
        return None
    effective_at = datetime.fromtimestamp(period_end, tz=timezone.utc)
    if sub.cancel_at_period_end:
        return SubscriptionTier.FREE, effective_at
    if not sub.schedule:
        return None
    schedule_id = sub.schedule if isinstance(sub.schedule, str) else sub.schedule.id
    schedule = await stripe.SubscriptionSchedule.retrieve_async(schedule_id)
    return _next_phase_tier_and_start(schedule, price_to_tier)