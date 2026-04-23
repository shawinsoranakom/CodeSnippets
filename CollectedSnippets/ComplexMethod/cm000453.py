async def test_high_concurrency_stress(server: SpinTestServer):
    """Stress test with many concurrent operations."""
    user_id = f"stress-test-{uuid4()}"
    await create_test_user(user_id)

    try:
        # Initial balance using internal method (bypasses Stripe)
        initial_balance = 10000  # $100
        await credit_system._add_transaction(
            user_id=user_id,
            amount=initial_balance,
            transaction_type=CreditTransactionType.TOP_UP,
            metadata=SafeJson({"test": "stress_test_balance"}),
        )

        # Run many concurrent operations
        async def random_operation(idx: int):
            operation = random.choice(["spend", "check"])

            if operation == "spend":
                amount = random.randint(1, 50)  # $0.01 to $0.50
                try:
                    return (
                        "spend",
                        amount,
                        await credit_system.spend_credits(
                            user_id,
                            amount,
                            UsageTransactionMetadata(reason=f"Stress {idx}"),
                        ),
                    )
                except InsufficientBalanceError:
                    return ("spend_failed", amount, None)
            else:
                balance = await credit_system.get_credits(user_id)
                return ("check", 0, balance)

        # Run 100 concurrent operations
        results = await asyncio.gather(
            *[random_operation(i) for i in range(100)], return_exceptions=True
        )

        # Calculate expected final balance
        total_spent = sum(
            r[1]
            for r in results
            if not isinstance(r, Exception) and isinstance(r, tuple) and r[0] == "spend"
        )
        expected_balance = initial_balance - total_spent

        # Verify final balance
        final_balance = await credit_system.get_credits(user_id)
        assert (
            final_balance == expected_balance
        ), f"Expected {expected_balance}, got {final_balance}"
        assert final_balance >= 0, "Balance went negative!"

    finally:
        await cleanup_test_user(user_id)