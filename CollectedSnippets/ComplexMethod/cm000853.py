async def _warn_if_stripe_subscription_drifts(
    user_id: str, new_tier: SubscriptionTier
) -> None:
    """Emit a WARNING when an admin tier override leaves an active Stripe sub on a
    mismatched price.

    The warning is diagnostic only: Stripe remains the billing source of truth,
    so the next ``customer.subscription.updated`` webhook will reset the DB
    tier. Surfacing the drift here lets ops catch admin overrides that bypass
    the intended Checkout / Portal cancel flows before users notice surprise
    charges.
    """
    # Local imports: see note in ``set_user_tier`` about the credit <-> rate_limit
    # circular. These helpers (``_get_active_subscription``,
    # ``get_subscription_price_id``) live in credit.py alongside the rest of
    # the Stripe billing code.
    from backend.data.credit import _get_active_subscription, get_subscription_price_id

    try:
        user = await get_user_by_id(user_id)
        if not getattr(user, "stripe_customer_id", None):
            return
        sub = await _get_active_subscription(user.stripe_customer_id)
        if sub is None:
            return
        items = sub["items"].data
        if not items:
            return
        price = items[0].price
        current_price_id = price if isinstance(price, str) else price.id
        # The LaunchDarkly-backed price lookup must live inside this try/except:
        # an LD SDK failure (network, token revoked) here would otherwise
        # propagate past set_user_tier's already-committed DB write and turn a
        # best-effort diagnostic into a 500 on admin tier writes.
        expected_price_id = await get_subscription_price_id(new_tier)
    except Exception:
        logger.debug(
            "_warn_if_stripe_subscription_drifts: drift lookup failed for"
            " user=%s; skipping drift warning",
            user_id,
            exc_info=True,
        )
        return
    if expected_price_id is not None and expected_price_id == current_price_id:
        return
    logger.warning(
        "Admin tier override will drift from Stripe: user=%s admin_tier=%s"
        " stripe_sub=%s stripe_price=%s expected_price=%s — the next"
        " customer.subscription.updated webhook will reconcile the DB tier"
        " back to whatever Stripe has; cancel or modify the Stripe subscription"
        " if you intended the admin override to stick.",
        user_id,
        new_tier.value,
        sub.id,
        current_price_id,
        expected_price_id,
    )