async def release_pending_subscription_schedule(user_id: str) -> bool:
    """Cancel any pending subscription change (scheduled downgrade or cancellation).

    Two pending-change mechanisms can be attached to a Stripe subscription:

    - **Subscription Schedule** (paid→paid downgrade): ``stripe.SubscriptionSchedule.release``
      detaches the schedule and lets the subscription continue on its current
      phase's price.
    - **cancel_at_period_end=True** (paid→FREE cancel): clearing that flag via
      ``stripe.Subscription.modify`` keeps the subscription active indefinitely.

    Returns True if a pending change was found and reverted, False otherwise.
    """
    user = await get_user_by_id(user_id)
    if not user.stripe_customer_id:
        return False

    sub = await _get_active_subscription(user.stripe_customer_id)
    if sub is None:
        return False

    sub_id = sub.id
    did_anything = False
    schedule_released = False
    schedule_id: str | None = None
    try:
        if sub.schedule:
            schedule_id = (
                sub.schedule if isinstance(sub.schedule, str) else sub.schedule.id
            )
            schedule_released = await _release_schedule_ignoring_terminal(
                schedule_id, "release_pending_subscription_schedule"
            )
            if schedule_released:
                logger.info(
                    "release_pending_subscription_schedule: released schedule %s for user %s",
                    schedule_id,
                    user_id,
                )
                did_anything = True
        if sub.cancel_at_period_end:
            try:
                await stripe.Subscription.modify_async(
                    sub_id, cancel_at_period_end=False
                )
            except stripe.StripeError:
                if schedule_released:
                    logger.exception(
                        "release_pending_subscription_schedule: partial release"
                        " — schedule %s released but cancel_at_period_end clear"
                        " failed on sub %s for user %s; manual reconciliation"
                        " may be needed",
                        schedule_id,
                        sub_id,
                        user_id,
                    )
                raise
            did_anything = True
            logger.info(
                "release_pending_subscription_schedule: cleared cancel_at_period_end"
                " on sub %s for user %s",
                sub_id,
                user_id,
            )
    finally:
        if did_anything:
            get_pending_subscription_change.cache_delete(user_id)
    return did_anything