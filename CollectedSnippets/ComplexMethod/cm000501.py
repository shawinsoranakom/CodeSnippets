async def handle_subscription_payment_failure(invoice: dict) -> None:
    """Handle a failed Stripe subscription payment.

    Tries to cover the invoice amount from the user's credit balance.

    - Balance sufficient  → deduct from balance, then pay the Stripe invoice so
      Stripe stops retrying it. The sub stays intact and the user keeps their tier.
    - Balance insufficient → cancel Stripe sub immediately, downgrade to FREE.
      Cancelling here avoids further Stripe retries on an invoice we cannot cover.
    """
    customer_id = invoice.get("customer")
    if not customer_id:
        logger.warning(
            "handle_subscription_payment_failure: missing customer in invoice; skipping"
        )
        return

    user = await User.prisma().find_first(where={"stripeCustomerId": customer_id})
    if not user:
        logger.warning(
            "handle_subscription_payment_failure: no user found for customer %s",
            customer_id,
        )
        return

    current_tier = user.subscriptionTier or SubscriptionTier.FREE
    if current_tier == SubscriptionTier.ENTERPRISE:
        logger.warning(
            "handle_subscription_payment_failure: skipping ENTERPRISE user %s"
            " (customer %s) — tier is admin-managed",
            user.id,
            customer_id,
        )
        return

    amount_due: int = invoice.get("amount_due", 0)
    sub_id: str = invoice.get("subscription", "")
    invoice_id: str = invoice.get("id", "")

    if amount_due <= 0:
        logger.info(
            "handle_subscription_payment_failure: amount_due=%d for user %s;"
            " nothing to deduct",
            amount_due,
            user.id,
        )
        return

    credit_model = UserCredit()
    try:
        await credit_model._add_transaction(
            user_id=user.id,
            amount=-amount_due,
            transaction_type=CreditTransactionType.SUBSCRIPTION,
            fail_insufficient_credits=True,
            # Use invoice_id as the idempotency key so that Stripe webhook retries
            # (e.g. on a transient stripe.Invoice.pay failure) do not double-charge.
            transaction_key=invoice_id or None,
            metadata=SafeJson(
                {
                    "stripe_customer_id": customer_id,
                    "stripe_subscription_id": sub_id,
                    "reason": "subscription_payment_failure_covered_by_balance",
                }
            ),
        )
        # Balance covered the invoice. Pay the Stripe invoice so Stripe's dunning
        # system stops retrying it — without this call Stripe would retry automatically
        # and re-trigger this webhook, causing double-deductions each retry cycle.
        if invoice_id:
            try:
                await run_in_threadpool(stripe.Invoice.pay, invoice_id)
            except stripe.StripeError:
                logger.warning(
                    "handle_subscription_payment_failure: balance deducted for user"
                    " %s but failed to mark invoice %s as paid; Stripe may retry",
                    user.id,
                    invoice_id,
                )
        logger.info(
            "handle_subscription_payment_failure: deducted %d cents from balance"
            " for user %s; Stripe invoice %s paid, sub %s intact, tier preserved",
            amount_due,
            user.id,
            invoice_id,
            sub_id,
        )
    except InsufficientBalanceError:
        # Balance insufficient — cancel Stripe subscription first, then downgrade DB.
        # Order matters: if we downgrade the DB first and the Stripe cancel fails, the
        # user is permanently stuck on FREE while Stripe continues billing them.
        # Cancelling Stripe first is safe: if the DB write then fails, the webhook
        # customer.subscription.deleted will fire and correct the tier eventually.
        logger.info(
            "handle_subscription_payment_failure: insufficient balance for user %s;"
            " cancelling Stripe sub %s then downgrading to FREE",
            user.id,
            sub_id,
        )
        try:
            await _cancel_customer_subscriptions(customer_id)
        except stripe.StripeError:
            logger.warning(
                "handle_subscription_payment_failure: failed to cancel Stripe sub %s"
                " for user %s (customer %s); skipping tier downgrade to avoid"
                " inconsistency — Stripe may continue retrying the invoice",
                sub_id,
                user.id,
                customer_id,
            )
            return
        await set_subscription_tier(user.id, SubscriptionTier.FREE)