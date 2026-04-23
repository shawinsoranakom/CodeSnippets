async def test_concurrent_spends_insufficient_balance(server: SpinTestServer):
    """Test that concurrent spends correctly enforce balance limits."""
    user_id = f"insufficient-test-{uuid4()}"
    await create_test_user(user_id)

    try:
        # Give user limited balance using internal method (bypasses Stripe)
        await credit_system._add_transaction(
            user_id=user_id,
            amount=500,
            transaction_type=CreditTransactionType.TOP_UP,
            metadata=SafeJson({"test": "limited_balance"}),
        )

        # Try to spend 10 x $1 concurrently (but only have $5)
        async def spend_one_dollar(idx: int):
            try:
                return await credit_system.spend_credits(
                    user_id,
                    100,  # $1
                    UsageTransactionMetadata(
                        graph_exec_id=f"insufficient-{idx}",
                        reason=f"Insufficient spend {idx}",
                    ),
                )
            except InsufficientBalanceError:
                return "FAILED"

        # Run 10 concurrent spends
        results = await asyncio.gather(
            *[spend_one_dollar(i) for i in range(10)], return_exceptions=True
        )

        # Count successful vs failed
        successful = [
            r
            for r in results
            if r not in ["FAILED", None] and not isinstance(r, Exception)
        ]
        failed = [r for r in results if r == "FAILED"]

        # Exactly 5 should succeed, 5 should fail
        assert len(successful) == 5, f"Expected 5 successful, got {len(successful)}"
        assert len(failed) == 5, f"Expected 5 failures, got {len(failed)}"

        # Final balance should be exactly 0
        final_balance = await credit_system.get_credits(user_id)
        assert final_balance == 0, f"Expected balance 0, got {final_balance}"

    finally:
        await cleanup_test_user(user_id)