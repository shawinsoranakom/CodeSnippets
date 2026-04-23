async def _schedule_downgrade_at_period_end(
    sub: stripe.Subscription,
    new_price_id: str,
    user_id: str,
    tier: SubscriptionTier,
) -> None:
    """Create a Subscription Schedule that defers a tier change to period end.

    Stripe's Subscription Schedule drives an existing subscription through a
    series of phases. By keeping the current price for the remainder of the
    billing period and switching to ``new_price_id`` afterwards, the user does
    NOT receive an immediate proration charge and keeps their current tier
    until period end.

    Stripe allows at most one active schedule per subscription and rejects
    ``SubscriptionSchedule.create`` if either (a) a schedule is already
    attached to the subscription or (b) ``cancel_at_period_end=True`` is set.
    Both conditions mean the user is overwriting a pending change they made
    earlier (e.g. BUSINESS→FREE cancel, now switching to BUSINESS→PRO
    downgrade). We clear the conflicting state first so the new schedule can
    be created. These defensive reads serialize through Stripe's own atomic
    operations — by the time modify/release returns, the subscription is in a
    known-clean state for the subsequent create.
    """
    sub_id = sub.id
    # ``sub["items"]`` (dict-item) rather than ``sub.items`` because the latter
    # is shadowed by Python's dict.items() method on StripeObject.
    items = sub["items"].data
    if not items:
        raise ValueError(f"Subscription {sub_id} has no items; cannot schedule")
    price = items[0].price
    current_price_id = price if isinstance(price, str) else price.id
    period_start: int = sub["current_period_start"]
    period_end: int = sub["current_period_end"]

    if sub.cancel_at_period_end:
        await stripe.Subscription.modify_async(sub_id, cancel_at_period_end=False)
        logger.info(
            "_schedule_downgrade_at_period_end: cleared cancel_at_period_end"
            " on sub %s for user %s before scheduling downgrade",
            sub_id,
            user_id,
        )
    if sub.schedule:
        existing_schedule_id = (
            sub.schedule if isinstance(sub.schedule, str) else sub.schedule.id
        )
        await _release_schedule_ignoring_terminal(
            existing_schedule_id, "_schedule_downgrade_at_period_end"
        )

    # Create + modify as a two-step transaction. If modify fails (network,
    # Stripe 500) the created schedule is orphaned AND attached to the
    # subscription, which blocks any future Stripe-side change until manually
    # released. Roll back by releasing the orphan, then re-raise so the caller
    # sees the original failure.
    schedule = await stripe.SubscriptionSchedule.create_async(from_subscription=sub_id)
    try:
        await stripe.SubscriptionSchedule.modify_async(
            schedule.id,
            phases=[
                {
                    "items": [{"price": current_price_id, "quantity": 1}],
                    "start_date": period_start,
                    "end_date": period_end,
                    "proration_behavior": "none",
                },
                {
                    "items": [{"price": new_price_id, "quantity": 1}],
                    "proration_behavior": "none",
                },
            ],
            metadata={"user_id": user_id, "pending_tier": tier.value},
        )
    except stripe.StripeError:
        logger.exception(
            "_schedule_downgrade_at_period_end: modify failed for schedule %s"
            " on sub %s user %s; attempting rollback release",
            schedule.id,
            sub_id,
            user_id,
        )
        try:
            await _release_schedule_ignoring_terminal(
                schedule.id, "_schedule_downgrade_at_period_end_rollback"
            )
        except stripe.StripeError:
            logger.exception(
                "_schedule_downgrade_at_period_end: rollback release also failed"
                " for orphaned schedule %s on sub %s user %s; manual cleanup"
                " required",
                schedule.id,
                sub_id,
                user_id,
            )
        raise
    logger.info(
        "modify_stripe_subscription_for_tier: scheduled sub %s downgrade for user %s → %s at %d",
        sub_id,
        user_id,
        tier,
        period_end,
    )