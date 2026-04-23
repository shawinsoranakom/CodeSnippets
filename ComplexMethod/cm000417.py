async def test_concurrent_large_refunds_no_underflow(server: SpinTestServer):
    """Test that concurrent large refunds don't cause race condition underflow."""
    credit_system = UserCredit()
    user_id = f"concurrent-underflow-test-{uuid4()}"
    await create_test_user(user_id)

    try:
        # Set up balance close to underflow threshold
        from prisma.models import UserBalance

        initial_balance = POSTGRES_INT_MIN + 1000  # Close to minimum
        await UserBalance.prisma().upsert(
            where={"userId": user_id},
            data={
                "create": {"userId": user_id, "balance": initial_balance},
                "update": {"balance": initial_balance},
            },
        )

        async def large_refund(amount: int, label: str):
            try:
                return await credit_system._add_transaction(
                    user_id=user_id,
                    amount=-amount,
                    transaction_type=CreditTransactionType.REFUND,
                    fail_insufficient_credits=False,
                )
            except Exception as e:
                return f"FAILED-{label}: {e}"

        # Run concurrent refunds that would cause underflow if not protected
        # Each refund of 500 would cause underflow: initial_balance + (-500) could go below POSTGRES_INT_MIN
        refund_amount = 500
        results = await asyncio.gather(
            large_refund(refund_amount, "A"),
            large_refund(refund_amount, "B"),
            large_refund(refund_amount, "C"),
            return_exceptions=True,
        )

        # Check all results are valid and no underflow occurred
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, tuple):
                balance, _ = result
                assert (
                    balance >= POSTGRES_INT_MIN
                ), f"Result {i} balance {balance} underflowed below {POSTGRES_INT_MIN}"
                valid_results.append(balance)
            elif isinstance(result, str) and "FAILED" in result:
                # Some operations might fail due to validation, that's okay
                pass
            else:
                # Unexpected exception
                assert not isinstance(
                    result, Exception
                ), f"Unexpected exception in result {i}: {result}"

        # At least one operation should succeed
        assert (
            len(valid_results) > 0
        ), f"At least one refund should succeed, got results: {results}"

        # All successful results should be >= POSTGRES_INT_MIN
        for balance in valid_results:
            assert (
                balance >= POSTGRES_INT_MIN
            ), f"Balance {balance} should not be below {POSTGRES_INT_MIN}"

        # Final balance should be valid and at or above POSTGRES_INT_MIN
        final_balance = await credit_system.get_credits(user_id)
        assert (
            final_balance >= POSTGRES_INT_MIN
        ), f"Final balance {final_balance} should not underflow below {POSTGRES_INT_MIN}"

    finally:
        await cleanup_test_user(user_id)