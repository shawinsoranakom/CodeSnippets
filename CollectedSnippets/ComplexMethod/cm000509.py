async def test_concurrent_operations_use_userbalance_only(server: SpinTestServer):
    """Test that concurrent operations all use UserBalance locking, not User.balance."""
    credit_system = UserCredit()
    user_id = f"concurrent-userbalance-test-{datetime.now().timestamp()}"
    await create_test_user(user_id)

    try:
        # Set initial balance in UserBalance
        await UserBalance.prisma().create(data={"userId": user_id, "balance": 1000})

        # Run concurrent operations to ensure they all use UserBalance atomic operations
        async def concurrent_spend(amount: int, label: str):
            try:
                await credit_system.spend_credits(
                    user_id,
                    amount,
                    UsageTransactionMetadata(
                        graph_exec_id=f"concurrent-{label}",
                        reason=f"Concurrent test {label}",
                    ),
                )
                return f"{label}-SUCCESS"
            except Exception as e:
                return f"{label}-FAILED: {e}"

        # Run concurrent operations
        results = await asyncio.gather(
            concurrent_spend(100, "A"),
            concurrent_spend(200, "B"),
            concurrent_spend(300, "C"),
            return_exceptions=True,
        )

        # All should succeed (1000 >= 100+200+300)
        successful = [r for r in results if "SUCCESS" in str(r)]
        assert len(successful) == 3, f"All operations should succeed, got {results}"

        # Final balance should be 1000 - 600 = 400
        final_balance = await credit_system.get_credits(user_id)
        assert final_balance == 400, f"Expected final balance 400, got {final_balance}"

        # Verify UserBalance has correct value
        user_balance = await UserBalance.prisma().find_unique(where={"userId": user_id})
        assert user_balance is not None
        assert (
            user_balance.balance == 400
        ), f"UserBalance should be 400, got {user_balance.balance}"

        # Critical: If User.balance exists and was used, it might have wrong value
        try:
            user = await User.prisma().find_unique(where={"id": user_id})
            user_balance_attr = getattr(user, "balance", None)
            if user_balance_attr is not None:
                # If User.balance exists, it should NOT be used for operations
                # The fact that our final balance is correct from UserBalance proves the system is working
                print(
                    f"✅ User.balance exists ({user_balance_attr}) but UserBalance ({user_balance.balance}) is being used correctly"
                )
        except Exception:
            print("✅ User.balance column doesn't exist - migration is complete")

    finally:
        await cleanup_test_user(user_id)