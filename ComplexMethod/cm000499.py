def _next_phase_tier_and_start(
    schedule: stripe.SubscriptionSchedule,
    price_to_tier: dict[str, SubscriptionTier],
) -> tuple[SubscriptionTier, datetime] | None:
    """Return (tier, start_datetime) of the phase that follows the active one.

    Using the phase's own ``start_date`` (not the subscription's current_period_end)
    is correct even for schedules created outside this flow — a dashboard-authored
    schedule can have phase transitions at arbitrary timestamps.
    """
    now = int(time.time())
    for phase in schedule.phases or []:
        if not isinstance(phase.start_date, int) or phase.start_date <= now:
            continue
        # ``phase["items"]`` because ``phase.items`` is shadowed by dict.items().
        items = phase["items"] or []
        if not items:
            continue
        price = items[0].price
        price_id = price if isinstance(price, str) else price.id
        if price_id in price_to_tier:
            return price_to_tier[price_id], datetime.fromtimestamp(
                phase.start_date, tz=timezone.utc
            )
        logger.warning(
            "next_phase_tier_and_start: unknown price %s on schedule %s",
            price_id,
            schedule.id,
        )
    return None