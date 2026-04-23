async def test_concurrent_refunds(server: SpinTestServer):
    """Test that concurrent refunds are handled atomically."""
    import asyncio

    topup_tx = await setup_test_user_with_topup()

    try:
        # Create multiple refund requests
        refund_requests = []
        for i in range(5):
            req = await CreditRefundRequest.prisma().create(
                data={
                    "userId": REFUND_TEST_USER_ID,
                    "amount": 100,  # $1 each
                    "transactionKey": topup_tx.transactionKey,
                    "reason": f"Test refund {i}",
                }
            )
            refund_requests.append(req)

        # Create refund tasks to run concurrently
        async def process_refund(index: int):
            refund = MagicMock(spec=stripe.Refund)
            refund.id = f"re_test_concurrent_{index}"
            refund.payment_intent = topup_tx.transactionKey
            refund.amount = 100  # $1 refund
            refund.status = "succeeded"
            refund.reason = "requested_by_customer"
            refund.created = int(datetime.now(timezone.utc).timestamp())

            try:
                await credit_system.deduct_credits(refund)
                return "success"
            except Exception as e:
                return f"error: {e}"

        # Run refunds concurrently
        results = await asyncio.gather(
            *[process_refund(i) for i in range(5)], return_exceptions=True
        )

        # All should succeed
        assert all(r == "success" for r in results), f"Some refunds failed: {results}"

        # Verify final balance - with non-atomic implementation, this will demonstrate race condition
        # EXPECTED BEHAVIOR: Due to race conditions, not all refunds will be properly processed
        # The balance will be incorrect (higher than expected) showing lost updates
        user_balance = await UserBalance.prisma().find_unique(
            where={"userId": REFUND_TEST_USER_ID}
        )
        assert user_balance is not None

        # With atomic implementation, this should be 500 (1000 - 5*100)
        # With current non-atomic implementation, this will likely be wrong due to race conditions
        print(f"DEBUG: Final balance = {user_balance.balance}, expected = 500")

        # With atomic implementation, all 5 refunds should process correctly
        assert (
            user_balance.balance == 500
        ), f"Expected balance 500 after 5 refunds of 100 each, got {user_balance.balance}"

        # Verify all refund transactions exist
        refund_txs = await CreditTransaction.prisma().find_many(
            where={
                "userId": REFUND_TEST_USER_ID,
                "type": CreditTransactionType.REFUND,
            }
        )
        assert (
            len(refund_txs) == 5
        ), f"Expected 5 refund transactions, got {len(refund_txs)}"

        running_balances: set[int] = {
            tx.runningBalance for tx in refund_txs if tx.runningBalance is not None
        }

        # Verify all balances are valid intermediate states
        for balance in running_balances:
            assert (
                500 <= balance <= 1000
            ), f"Invalid balance {balance}, should be between 500 and 1000"

        # Final balance should be present
        assert (
            500 in running_balances
        ), f"Final balance 500 should be in {running_balances}"

        # All balances should be unique and form a valid sequence
        sorted_balances = sorted(running_balances, reverse=True)
        assert (
            len(sorted_balances) == 5
        ), f"Expected 5 unique balances, got {len(sorted_balances)}"

    finally:
        await cleanup_test_user()