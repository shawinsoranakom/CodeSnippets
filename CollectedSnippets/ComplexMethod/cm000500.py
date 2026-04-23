async def sync_subscription_from_stripe(stripe_subscription: dict) -> None:
    """Update User.subscriptionTier from a Stripe subscription object.

    Expected shape of stripe_subscription (subset of Stripe's Subscription object):
        customer: str                  — Stripe customer ID
        status:   str                  — "active" | "trialing" | "canceled" | ...
        id:       str                  — Stripe subscription ID
        items.data[].price.id: str     — Stripe price ID identifying the tier
    """
    customer_id = stripe_subscription.get("customer")
    if not customer_id:
        logger.warning(
            "sync_subscription_from_stripe: missing 'customer' field in event, "
            "skipping (keys: %s)",
            list(stripe_subscription.keys()),
        )
        return
    user = await User.prisma().find_first(where={"stripeCustomerId": customer_id})
    if not user:
        logger.warning(
            "sync_subscription_from_stripe: no user for customer %s", customer_id
        )
        return
    # Cross-check: if the subscription carries a metadata.user_id (set during
    # Checkout Session creation), verify it matches the user we found via
    # stripeCustomerId.  A mismatch indicates a customer↔user mapping
    # inconsistency — updating the wrong user's tier would be a data-corruption
    # bug, so we log loudly and bail out.  Absence of metadata.user_id (e.g.
    # subscriptions created outside the Checkout flow) is not an error — we
    # simply skip the check and proceed with the customer-ID-based lookup.
    metadata = stripe_subscription.get("metadata") or {}
    metadata_user_id = metadata.get("user_id") if isinstance(metadata, dict) else None
    if metadata_user_id and metadata_user_id != user.id:
        logger.error(
            "sync_subscription_from_stripe: metadata.user_id=%s does not match"
            " user.id=%s found via stripeCustomerId=%s — refusing to update tier"
            " to avoid corrupting the wrong user's subscription state",
            metadata_user_id,
            user.id,
            customer_id,
        )
        return
    # ENTERPRISE tiers are admin-managed. Never let a Stripe webhook flip an
    # ENTERPRISE user to a different tier — if a user on ENTERPRISE somehow has
    # a self-service Stripe sub, it's a data-consistency issue for an operator,
    # not something the webhook should automatically "fix".
    current_tier = user.subscriptionTier or SubscriptionTier.FREE
    if current_tier == SubscriptionTier.ENTERPRISE:
        logger.warning(
            "sync_subscription_from_stripe: refusing to overwrite ENTERPRISE tier"
            " for user %s (customer %s); event status=%s",
            user.id,
            customer_id,
            stripe_subscription.get("status", ""),
        )
        return
    status = stripe_subscription.get("status", "")
    new_sub_id = stripe_subscription.get("id", "")
    if status in ("active", "trialing"):
        price_id = ""
        items = stripe_subscription.get("items", {}).get("data", [])
        if items:
            price_id = items[0].get("price", {}).get("id", "")
        pro_price, biz_price = await asyncio.gather(
            get_subscription_price_id(SubscriptionTier.PRO),
            get_subscription_price_id(SubscriptionTier.BUSINESS),
        )
        if price_id and pro_price and price_id == pro_price:
            tier = SubscriptionTier.PRO
        elif price_id and biz_price and price_id == biz_price:
            tier = SubscriptionTier.BUSINESS
        else:
            # Unknown or unconfigured price ID — preserve the user's current tier
            # rather than defaulting to FREE. This prevents accidental downgrades
            # during a price migration or when LD flags are not yet configured.
            logger.warning(
                "sync_subscription_from_stripe: unknown price %s for customer %s,"
                " preserving current tier",
                price_id,
                customer_id,
            )
            return
    else:
        # A subscription was cancelled or ended. DO NOT unconditionally downgrade
        # to FREE — Stripe does not guarantee webhook delivery order, so a
        # `customer.subscription.deleted` for the OLD sub can arrive after we've
        # already processed `customer.subscription.created` for a new paid sub.
        # Ask Stripe whether any OTHER active/trialing subs exist for this
        # customer; if they do, keep the user's current tier (the other sub's
        # own event will/has already set the correct tier).
        try:
            other_subs_active, other_subs_trialing = await asyncio.gather(
                run_in_threadpool(
                    stripe.Subscription.list,
                    customer=customer_id,
                    status="active",
                    limit=10,
                ),
                run_in_threadpool(
                    stripe.Subscription.list,
                    customer=customer_id,
                    status="trialing",
                    limit=10,
                ),
            )
        except stripe.StripeError:
            logger.warning(
                "sync_subscription_from_stripe: could not verify other active"
                " subs for customer %s on cancel event %s; preserving current"
                " tier to avoid an unsafe downgrade",
                customer_id,
                new_sub_id,
            )
            return
        # Filter out the cancelled subscription to check if other active subs
        # exist. When new_sub_id is empty (malformed event with no 'id' field),
        # we cannot safely exclude any sub — preserve current tier to avoid
        # an unsafe downgrade on a malformed webhook payload.
        if not new_sub_id:
            logger.warning(
                "sync_subscription_from_stripe: cancel event missing 'id' field"
                " for customer %s; preserving current tier",
                customer_id,
            )
            return
        other_active_ids = {sub["id"] for sub in other_subs_active.data} - {new_sub_id}
        other_trialing_ids = {sub["id"] for sub in other_subs_trialing.data} - {
            new_sub_id
        }
        still_has_active_sub = bool(other_active_ids or other_trialing_ids)
        if still_has_active_sub:
            logger.info(
                "sync_subscription_from_stripe: sub %s cancelled but customer %s"
                " still has another active sub; keeping tier %s",
                new_sub_id,
                customer_id,
                current_tier.value,
            )
            return
        tier = SubscriptionTier.FREE
    # Idempotency: Stripe retries webhooks on delivery failure, and several event
    # types map to the same final tier. Skip the DB write + cache invalidation
    # when the tier is already correct to avoid redundant writes on replay.
    if current_tier == tier:
        return
    # When a new subscription becomes active (e.g. paid-to-paid tier upgrade
    # via a fresh Checkout Session), cancel any OTHER active subscriptions for
    # the same customer so the user isn't billed twice. We do this in the
    # webhook rather than the API handler so that abandoning the checkout
    # doesn't leave the user without a subscription.
    # IMPORTANT: this runs AFTER the idempotency check above so that webhook
    # replays for an already-applied event do NOT trigger another cleanup round
    # (which could otherwise cancel a legitimately new subscription the user
    # signed up for between the original event and its replay).
    if status in ("active", "trialing") and new_sub_id:
        # NOTE: paid-to-paid upgrade race (e.g. PRO → BUSINESS):
        # _cleanup_stale_subscriptions cancels the old PRO sub before
        # set_subscription_tier writes BUSINESS to the DB.  If Stripe delivers
        # the PRO `customer.subscription.deleted` event concurrently and it
        # processes after the PRO cancel but before set_subscription_tier
        # commits, the user could momentarily appear as FREE in the DB.
        # This window is very short in practice (two sequential awaits),
        # but is a known limitation of the current webhook-driven approach.
        # A future improvement would be to write the new tier first, then
        # cancel the old sub.
        await _cleanup_stale_subscriptions(customer_id, new_sub_id)
    await set_subscription_tier(user.id, tier)
    # Tier changed — bust any cached pending-change view so the next
    # dashboard fetch reflects the new state immediately.
    get_pending_subscription_change.cache_delete(user.id)