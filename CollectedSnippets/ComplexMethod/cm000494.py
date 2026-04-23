async def _cancel_customer_subscriptions(
    customer_id: str,
    exclude_sub_id: str | None = None,
    at_period_end: bool = False,
) -> int:
    """Cancel all billable Stripe subscriptions for a customer, optionally excluding one.

    Cancels both ``active`` and ``trialing`` subscriptions, since trialing subs will
    start billing once the trial ends and must be cleaned up on downgrade/upgrade to
    avoid double-charging or charging users who intended to cancel.

    When ``at_period_end=True``, schedules cancellation at the end of the current
    billing period instead of cancelling immediately — the user keeps their tier
    until the period ends, then ``customer.subscription.deleted`` fires and the
    webhook downgrades them to FREE.

    Wraps every synchronous Stripe SDK call with run_in_threadpool so the async event
    loop is never blocked. Raises stripe.StripeError on list/cancel failure so callers
    that need strict consistency can react; cleanup callers can catch and log instead.

    Returns the number of subscriptions cancelled/scheduled for cancellation.
    """
    # Query active and trialing separately; Stripe's list API accepts a single status
    # filter at a time (no OR), and we explicitly want to skip canceled/incomplete/
    # past_due subs rather than filter them out client-side via status="all".
    seen_ids: set[str] = set()
    for status in ("active", "trialing"):
        subscriptions = await run_in_threadpool(
            stripe.Subscription.list, customer=customer_id, status=status, limit=10
        )
        # Iterate only the first page (up to 10); avoid auto_paging_iter which would
        # trigger additional sync HTTP calls inside the event loop.
        if subscriptions.has_more:
            logger.error(
                "_cancel_customer_subscriptions: customer %s has more than 10 %s"
                " subscriptions — only the first page was processed; remaining"
                " subscriptions were NOT cancelled",
                customer_id,
                status,
            )
        for sub in subscriptions.data:
            sub_id = sub["id"]
            if exclude_sub_id and sub_id == exclude_sub_id:
                continue
            if sub_id in seen_ids:
                continue
            seen_ids.add(sub_id)
            if at_period_end:
                # Stripe rejects modify(cancel_at_period_end=True) with 400 when a
                # Subscription Schedule is attached (e.g. the user previously
                # queued a paid→paid downgrade and is now clicking "Cancel").
                # Release the schedule first so the cancel flag can be set; the
                # schedule's pending phase change is superseded by the cancel.
                existing_schedule = sub.schedule
                if existing_schedule:
                    schedule_id = (
                        existing_schedule
                        if isinstance(existing_schedule, str)
                        else existing_schedule.id
                    )
                    await _release_schedule_ignoring_terminal(
                        schedule_id, "_cancel_customer_subscriptions"
                    )
                await run_in_threadpool(
                    stripe.Subscription.modify, sub_id, cancel_at_period_end=True
                )
            else:
                await run_in_threadpool(stripe.Subscription.cancel, sub_id)
    return len(seen_ids)