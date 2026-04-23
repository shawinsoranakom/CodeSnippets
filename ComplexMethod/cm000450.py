async def test_concurrent_spends_same_user(server: SpinTestServer):
    """Test multiple concurrent spends from the same user don't cause race conditions."""
    user_id = f"concurrent-test-{uuid4()}"
    await create_test_user(user_id)

    try:
        # Give user initial balance using internal method (bypasses Stripe)
        await credit_system._add_transaction(
            user_id=user_id,
            amount=1000,
            transaction_type=CreditTransactionType.TOP_UP,
            metadata=SafeJson({"test": "initial_balance"}),
        )

        # Try to spend 10 x $1 concurrently
        async def spend_one_dollar(idx: int):
            try:
                return await credit_system.spend_credits(
                    user_id,
                    100,  # $1
                    UsageTransactionMetadata(
                        graph_exec_id=f"concurrent-{idx}",
                        reason=f"Concurrent spend {idx}",
                    ),
                )
            except InsufficientBalanceError:
                return None

        # Run 10 concurrent spends
        results = await asyncio.gather(
            *[spend_one_dollar(i) for i in range(10)], return_exceptions=True
        )

        # Count successful spends
        successful = [
            r for r in results if r is not None and not isinstance(r, Exception)
        ]
        failed = [r for r in results if isinstance(r, InsufficientBalanceError)]

        # All 10 should succeed since we have exactly $10
        assert len(successful) == 10, f"Expected 10 successful, got {len(successful)}"
        assert len(failed) == 0, f"Expected 0 failures, got {len(failed)}"

        # Final balance should be exactly 0
        final_balance = await credit_system.get_credits(user_id)
        assert final_balance == 0, f"Expected balance 0, got {final_balance}"

        # Verify transaction history is consistent
        transactions = await CreditTransaction.prisma().find_many(
            where={"userId": user_id, "type": prisma.enums.CreditTransactionType.USAGE}
        )
        assert (
            len(transactions) == 10
        ), f"Expected 10 transactions, got {len(transactions)}"

    finally:
        await cleanup_test_user(user_id)