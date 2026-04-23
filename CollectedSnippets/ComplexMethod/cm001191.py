async def stripe_webhook(request: Request):
    webhook_secret = settings.secrets.stripe_webhook_secret
    if not webhook_secret:
        # Guard: an empty secret allows HMAC forgery (attacker can compute a valid
        # signature over the same empty key). Reject all webhook calls when unconfigured.
        logger.error(
            "stripe_webhook: STRIPE_WEBHOOK_SECRET is not configured — "
            "rejecting request to prevent signature bypass"
        )
        raise HTTPException(status_code=503, detail="Webhook not configured")

    # Get the raw request body
    payload = await request.body()
    # Get the signature header
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except ValueError:
        # Invalid payload
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.SignatureVerificationError:
        # Invalid signature
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Defensive payload extraction. A malformed payload (missing/non-dict
    # `data.object`, missing `id`) would otherwise raise KeyError/TypeError
    # AFTER signature verification — which Stripe interprets as a delivery
    # failure and retries forever, while spamming Sentry with no useful info.
    # Acknowledge with 200 and a warning so Stripe stops retrying.
    event_type = event.get("type", "")
    event_data = event.get("data") or {}
    data_object = event_data.get("object") if isinstance(event_data, dict) else None
    if not isinstance(data_object, dict):
        logger.warning(
            "stripe_webhook: %s missing or non-dict data.object; ignoring",
            event_type,
        )
        return Response(status_code=200)

    if event_type in (
        "checkout.session.completed",
        "checkout.session.async_payment_succeeded",
    ):
        session_id = data_object.get("id")
        if not session_id:
            logger.warning(
                "stripe_webhook: %s missing data.object.id; ignoring", event_type
            )
            return Response(status_code=200)
        await UserCredit().fulfill_checkout(session_id=session_id)

    if event_type in (
        "customer.subscription.created",
        "customer.subscription.updated",
        "customer.subscription.deleted",
    ):
        await sync_subscription_from_stripe(data_object)

    # `subscription_schedule.updated` is deliberately omitted: our own
    # `SubscriptionSchedule.create` + `.modify` calls in
    # `_schedule_downgrade_at_period_end` would fire that event right back at us
    # and loop redundant traffic through this handler. We only care about state
    # transitions (released / completed); phase advance to the new price is
    # already covered by `customer.subscription.updated`.
    if event_type in (
        "subscription_schedule.released",
        "subscription_schedule.completed",
    ):
        await sync_subscription_schedule_from_stripe(data_object)

    if event_type == "invoice.payment_failed":
        await handle_subscription_payment_failure(data_object)

    # `handle_dispute` and `deduct_credits` expect Stripe SDK typed objects
    # (Dispute/Refund). The Stripe webhook payload's `data.object` is a
    # StripeObject (a dict subclass) carrying that runtime shape, so we cast
    # to satisfy the type checker without changing runtime behaviour.
    if event_type == "charge.dispute.created":
        await UserCredit().handle_dispute(cast(stripe.Dispute, data_object))

    if event_type == "refund.created" or event_type == "charge.dispute.closed":
        await UserCredit().deduct_credits(
            cast("stripe.Refund | stripe.Dispute", data_object)
        )

    return Response(status_code=200)