async def update_subscription_tier(
    request: SubscriptionTierRequest,
    user_id: Annotated[str, Security(get_user_id)],
) -> SubscriptionStatusResponse:
    # Pydantic validates tier is one of FREE/PRO/BUSINESS via Literal type.
    tier = SubscriptionTier(request.tier)

    # ENTERPRISE tier is admin-managed — block self-service changes from ENTERPRISE users.
    user = await get_user_by_id(user_id)
    if (user.subscription_tier or SubscriptionTier.FREE) == SubscriptionTier.ENTERPRISE:
        raise HTTPException(
            status_code=403,
            detail="ENTERPRISE subscription changes must be managed by an administrator",
        )

    # Same-tier request = "stay on my current tier" = cancel any pending
    # scheduled change (paid→paid downgrade or paid→FREE cancel). This is the
    # collapsed behaviour that replaces the old /credits/subscription/cancel-pending
    # route. Safe when no pending change exists: release_pending_subscription_schedule
    # returns False and we simply return the current status.
    if (user.subscription_tier or SubscriptionTier.FREE) == tier:
        try:
            await release_pending_subscription_schedule(user_id)
        except stripe.StripeError as e:
            logger.exception(
                "Stripe error releasing pending subscription change for user %s: %s",
                user_id,
                e,
            )
            raise HTTPException(
                status_code=502,
                detail=(
                    "Unable to cancel the pending subscription change right now. "
                    "Please try again or contact support."
                ),
            )
        return await get_subscription_status(user_id)

    payment_enabled = await is_feature_enabled(
        Flag.ENABLE_PLATFORM_PAYMENT, user_id, default=False
    )

    # Downgrade to FREE: schedule Stripe cancellation at period end so the user
    # keeps their tier for the time they already paid for. The DB tier is NOT
    # updated here when a subscription exists — the customer.subscription.deleted
    # webhook fires at period end and downgrades to FREE then.
    # Exception: if the user has no active Stripe subscription (e.g. admin-granted
    # tier), cancel_stripe_subscription returns False and we update the DB tier
    # immediately since no webhook will ever fire.
    # When payment is disabled entirely, update the DB tier directly.
    if tier == SubscriptionTier.FREE:
        if payment_enabled:
            try:
                had_subscription = await cancel_stripe_subscription(user_id)
            except stripe.StripeError as e:
                # Log full Stripe error server-side but return a generic message
                # to the client — raw Stripe errors can leak customer/sub IDs and
                # infrastructure config details.
                logger.exception(
                    "Stripe error cancelling subscription for user %s: %s",
                    user_id,
                    e,
                )
                raise HTTPException(
                    status_code=502,
                    detail=(
                        "Unable to cancel your subscription right now. "
                        "Please try again or contact support."
                    ),
                )
            if not had_subscription:
                # No active Stripe subscription found — the user was on an
                # admin-granted tier. Update DB immediately since the
                # subscription.deleted webhook will never fire.
                await set_subscription_tier(user_id, tier)
            return await get_subscription_status(user_id)
        await set_subscription_tier(user_id, tier)
        return await get_subscription_status(user_id)

    # Paid tier changes require payment to be enabled — block self-service upgrades
    # when the flag is off.  Admins use the /api/admin/ routes to set tiers directly.
    if not payment_enabled:
        raise HTTPException(
            status_code=422,
            detail=f"Subscription not available for tier {tier}",
        )

    # Paid→paid tier change: if the user already has a Stripe subscription,
    # modify it in-place with proration instead of creating a new Checkout
    # Session. This preserves remaining paid time and avoids double-charging.
    # The customer.subscription.updated webhook fires and updates the DB tier.
    current_tier = user.subscription_tier or SubscriptionTier.FREE
    if current_tier in (SubscriptionTier.PRO, SubscriptionTier.BUSINESS):
        try:
            modified = await modify_stripe_subscription_for_tier(user_id, tier)
            if modified:
                return await get_subscription_status(user_id)
            # modify_stripe_subscription_for_tier returns False when no active
            # Stripe subscription exists — i.e. the user has an admin-granted
            # paid tier with no Stripe record.  In that case, update the DB
            # tier directly (same as the FREE-downgrade path for admin-granted
            # users) rather than sending them through a new Checkout Session.
            await set_subscription_tier(user_id, tier)
            return await get_subscription_status(user_id)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
        except stripe.StripeError as e:
            logger.exception(
                "Stripe error modifying subscription for user %s: %s", user_id, e
            )
            raise HTTPException(
                status_code=502,
                detail=(
                    "Unable to update your subscription right now. "
                    "Please try again or contact support."
                ),
            )

    # Paid upgrade from FREE → create Stripe Checkout Session.
    if not request.success_url or not request.cancel_url:
        raise HTTPException(
            status_code=422,
            detail="success_url and cancel_url are required for paid tier upgrades",
        )
    # Open-redirect protection: both URLs must point to the configured frontend
    # origin, otherwise an attacker could use our Stripe integration as a
    # redirector to arbitrary phishing sites.
    #
    # Fail early with a clear 503 if the server is misconfigured (neither
    # frontend_base_url nor platform_base_url set), so operators get an
    # actionable error instead of the misleading "must match the platform
    # frontend origin" 422 that _validate_checkout_redirect_url would otherwise
    # produce when `allowed` is empty.
    if not (settings.config.frontend_base_url or settings.config.platform_base_url):
        logger.error(
            "update_subscription_tier: neither frontend_base_url nor "
            "platform_base_url is configured; cannot validate checkout redirect URLs"
        )
        raise HTTPException(
            status_code=503,
            detail=(
                "Payment redirect URLs cannot be validated: "
                "frontend_base_url or platform_base_url must be set on the server."
            ),
        )
    if not _validate_checkout_redirect_url(
        request.success_url
    ) or not _validate_checkout_redirect_url(request.cancel_url):
        raise HTTPException(
            status_code=422,
            detail="success_url and cancel_url must match the platform frontend origin",
        )
    try:
        url = await create_subscription_checkout(
            user_id=user_id,
            tier=tier,
            success_url=request.success_url,
            cancel_url=request.cancel_url,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except stripe.StripeError as e:
        logger.exception(
            "Stripe error creating checkout session for user %s: %s", user_id, e
        )
        raise HTTPException(
            status_code=502,
            detail=(
                "Unable to start checkout right now. "
                "Please try again or contact support."
            ),
        )

    status = await get_subscription_status(user_id)
    status.url = url
    return status