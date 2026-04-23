async def test_user_balance_migration_complete(server: SpinTestServer):
    """Test that User table balance is never used and UserBalance is source of truth."""
    credit_system = UserCredit()
    user_id = f"migration-test-{datetime.now().timestamp()}"
    await create_test_user(user_id)

    try:
        # 1. Verify User table does NOT have balance set initially
        user = await User.prisma().find_unique(where={"id": user_id})
        assert user is not None
        # User.balance should not exist or should be None/0 if it exists
        user_balance_attr = getattr(user, "balance", None)
        if user_balance_attr is not None:
            assert (
                user_balance_attr == 0 or user_balance_attr is None
            ), f"User.balance should be 0 or None, got {user_balance_attr}"

        # 2. Perform various credit operations using internal method (bypasses Stripe)
        await credit_system._add_transaction(
            user_id=user_id,
            amount=1000,
            transaction_type=CreditTransactionType.TOP_UP,
            metadata=SafeJson({"test": "migration_test"}),
        )
        balance1 = await credit_system.get_credits(user_id)
        assert balance1 == 1000

        await credit_system.spend_credits(
            user_id,
            300,
            UsageTransactionMetadata(
                graph_exec_id="test", reason="Migration test spend"
            ),
        )
        balance2 = await credit_system.get_credits(user_id)
        assert balance2 == 700

        # 3. Verify UserBalance table has correct values
        user_balance = await UserBalance.prisma().find_unique(where={"userId": user_id})
        assert user_balance is not None
        assert (
            user_balance.balance == 700
        ), f"UserBalance should be 700, got {user_balance.balance}"

        # 4. CRITICAL: Verify User.balance is NEVER updated during operations
        user_after = await User.prisma().find_unique(where={"id": user_id})
        assert user_after is not None
        user_balance_after = getattr(user_after, "balance", None)
        if user_balance_after is not None:
            # If User.balance exists, it should still be 0 (never updated)
            assert (
                user_balance_after == 0 or user_balance_after is None
            ), f"User.balance should remain 0/None after operations, got {user_balance_after}. This indicates User.balance is still being used!"

        # 5. Verify get_credits always returns UserBalance value, not User.balance
        final_balance = await credit_system.get_credits(user_id)
        assert (
            final_balance == user_balance.balance
        ), f"get_credits should return UserBalance value {user_balance.balance}, got {final_balance}"

    finally:
        await cleanup_test_user(user_id)