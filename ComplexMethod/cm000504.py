async def deduct_credits(self, request: stripe.Refund | stripe.Dispute):
        if isinstance(request, stripe.Refund) and request.status != "succeeded":
            logger.warning(
                f"Skip processing refund #{request.id} with status {request.status}"
            )
            return

        if isinstance(request, stripe.Dispute) and request.status != "lost":
            logger.warning(
                f"Skip processing dispute #{request.id} with status {request.status}"
            )
            return

        transaction = await CreditTransaction.prisma().find_first_or_raise(
            where={
                "transactionKey": str(request.payment_intent),
                "isActive": True,
                "type": CreditTransactionType.TOP_UP,
            }
        )
        if request.amount <= 0 or request.amount > transaction.amount:
            raise AssertionError(
                f"Invalid amount to deduct ${request.amount / 100} from ${transaction.amount / 100} top-up"
            )

        balance, _ = await self._add_transaction(
            user_id=transaction.userId,
            amount=-request.amount,
            transaction_type=CreditTransactionType.REFUND,
            transaction_key=request.id,
            metadata=SafeJson(request),
            fail_insufficient_credits=False,
        )

        # Update the result of the refund request if it exists.
        await CreditRefundRequest.prisma().update_many(
            where={
                "userId": transaction.userId,
                "transactionKey": transaction.transactionKey,
            },
            data={
                "amount": request.amount,
                "status": CreditRefundRequestStatus.APPROVED,
                "result": "The refund request has been approved, the amount will be credited back to your account.",
            },
        )

        user_data = await get_user_by_id(transaction.userId)
        await self._send_refund_notification(
            RefundRequestData(
                user_id=user_data.id,
                user_name=user_data.name or "AutoGPT Platform User",
                user_email=user_data.email,
                transaction_id=transaction.transactionKey,
                refund_request_id=request.id,
                reason=str(request.reason or "-"),
                amount=transaction.amount,
                balance=balance,
            ),
            NotificationType.REFUND_PROCESSED,
        )