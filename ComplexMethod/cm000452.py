async def test_race_condition_exact_balance(server: SpinTestServer):
    """Test spending exact balance amount concurrently doesn't go negative."""
    user_id = f"exact-balance-{uuid4()}"
    await create_test_user(user_id)

    try:
        # Give exact amount using internal method (bypasses Stripe)
        await credit_system._add_transaction(
            user_id=user_id,
            amount=100,
            transaction_type=CreditTransactionType.TOP_UP,
            metadata=SafeJson({"test": "exact_amount"}),
        )

        # Try to spend $1 twice concurrently
        async def spend_exact():
            try:
                return await credit_system.spend_credits(
                    user_id, 100, UsageTransactionMetadata(reason="Exact spend")
                )
            except InsufficientBalanceError:
                return "FAILED"

        # Both try to spend the full balance
        result1, result2 = await asyncio.gather(spend_exact(), spend_exact())

        # Exactly one should succeed
        results = [result1, result2]
        successful = [
            r for r in results if r != "FAILED" and not isinstance(r, Exception)
        ]
        failed = [r for r in results if r == "FAILED"]

        assert len(successful) == 1, f"Expected 1 success, got {len(successful)}"
        assert len(failed) == 1, f"Expected 1 failure, got {len(failed)}"

        # Balance should be exactly 0, never negative
        final_balance = await credit_system.get_credits(user_id)
        assert final_balance == 0, f"Expected balance 0, got {final_balance}"

    finally:
        await cleanup_test_user(user_id)