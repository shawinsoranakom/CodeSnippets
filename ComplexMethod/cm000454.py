async def test_concurrent_multiple_spends_sufficient_balance(server: SpinTestServer):
    """Test multiple concurrent spends when there's sufficient balance for all."""
    user_id = f"multi-spend-test-{uuid4()}"
    await create_test_user(user_id)

    try:
        # Give user 150 balance ($1.50) using internal method (bypasses Stripe)
        await credit_system._add_transaction(
            user_id=user_id,
            amount=150,
            transaction_type=CreditTransactionType.TOP_UP,
            metadata=SafeJson({"test": "sufficient_balance"}),
        )

        # Track individual timing to see serialization
        timings = {}

        async def spend_with_detailed_timing(amount: int, label: str):
            start = asyncio.get_event_loop().time()
            try:
                await credit_system.spend_credits(
                    user_id,
                    amount,
                    UsageTransactionMetadata(
                        graph_exec_id=f"concurrent-{label}",
                        reason=f"Concurrent spend {label}",
                    ),
                )
                end = asyncio.get_event_loop().time()
                timings[label] = {"start": start, "end": end, "duration": end - start}
                return f"{label}-SUCCESS"
            except Exception as e:
                end = asyncio.get_event_loop().time()
                timings[label] = {
                    "start": start,
                    "end": end,
                    "duration": end - start,
                    "error": str(e),
                }
                return f"{label}-FAILED: {e}"

        # Run concurrent spends: 10, 20, 30 (total 60, well under 150)
        overall_start = asyncio.get_event_loop().time()
        results = await asyncio.gather(
            spend_with_detailed_timing(10, "spend-10"),
            spend_with_detailed_timing(20, "spend-20"),
            spend_with_detailed_timing(30, "spend-30"),
            return_exceptions=True,
        )
        overall_end = asyncio.get_event_loop().time()

        print(f"Results: {results}")
        print(f"Overall duration: {overall_end - overall_start:.4f}s")

        # Analyze timing to detect serialization vs true concurrency
        print("\nTiming analysis:")
        for label, timing in timings.items():
            print(
                f"  {label}: started at {timing['start']:.4f}, ended at {timing['end']:.4f}, duration {timing['duration']:.4f}s"
            )

        # Check if operations overlapped (true concurrency) or were serialized
        sorted_timings = sorted(timings.items(), key=lambda x: x[1]["start"])
        print("\nExecution order by start time:")
        for i, (label, timing) in enumerate(sorted_timings):
            print(f"  {i+1}. {label}: {timing['start']:.4f} -> {timing['end']:.4f}")

        # Check for overlap (true concurrency) vs serialization
        overlaps = []
        for i in range(len(sorted_timings) - 1):
            current = sorted_timings[i]
            next_op = sorted_timings[i + 1]
            if current[1]["end"] > next_op[1]["start"]:
                overlaps.append(f"{current[0]} overlaps with {next_op[0]}")

        if overlaps:
            print(f"✅ TRUE CONCURRENCY detected: {overlaps}")
        else:
            print("🔒 SERIALIZATION detected: No overlapping execution times")

        # Check final balance
        final_balance = await credit_system.get_credits(user_id)
        print(f"Final balance: {final_balance}")

        # Count successes/failures
        successful = [r for r in results if "SUCCESS" in str(r)]
        failed = [r for r in results if "FAILED" in str(r)]

        print(f"Successful: {len(successful)}, Failed: {len(failed)}")

        # All should succeed since 150 - (10 + 20 + 30) = 90 > 0
        assert (
            len(successful) == 3
        ), f"Expected all 3 to succeed, got {len(successful)} successes: {results}"
        assert final_balance == 90, f"Expected balance 90, got {final_balance}"

        # Check transaction timestamps to confirm database-level serialization
        transactions = await CreditTransaction.prisma().find_many(
            where={"userId": user_id, "type": prisma.enums.CreditTransactionType.USAGE},
            order={"createdAt": "asc"},
        )
        print("\nDatabase transaction order (by createdAt):")
        for i, tx in enumerate(transactions):
            print(
                f"  {i+1}. Amount {tx.amount}, Running balance: {tx.runningBalance}, Created: {tx.createdAt}"
            )

        # Verify running balances are chronologically consistent (ordered by createdAt)
        actual_balances = [
            tx.runningBalance for tx in transactions if tx.runningBalance is not None
        ]
        print(f"Running balances: {actual_balances}")

        # The balances should be valid intermediate states regardless of execution order
        # Starting balance: 150, spending 10+20+30=60, so final should be 90
        # The intermediate balances depend on execution order but should all be valid
        expected_possible_balances = {
            # If order is 10, 20, 30: [140, 120, 90]
            # If order is 10, 30, 20: [140, 110, 90]
            # If order is 20, 10, 30: [130, 120, 90]
            # If order is 20, 30, 10: [130, 100, 90]
            # If order is 30, 10, 20: [120, 110, 90]
            # If order is 30, 20, 10: [120, 100, 90]
            90,
            100,
            110,
            120,
            130,
            140,  # All possible intermediate balances
        }

        # Verify all balances are valid intermediate states
        for balance in actual_balances:
            assert (
                balance in expected_possible_balances
            ), f"Invalid balance {balance}, expected one of {expected_possible_balances}"

        # Final balance should always be 90 (150 - 60)
        assert (
            min(actual_balances) == 90
        ), f"Final balance should be 90, got {min(actual_balances)}"

        # The final transaction should always have balance 90
        # The other transactions should have valid intermediate balances
        assert (
            90 in actual_balances
        ), f"Final balance 90 should be in actual_balances: {actual_balances}"

        # All balances should be >= 90 (the final state)
        assert all(
            balance >= 90 for balance in actual_balances
        ), f"All balances should be >= 90, got {actual_balances}"

        # CRITICAL: Transactions are atomic but can complete in any order
        # What matters is that all running balances are valid intermediate states
        # Each balance should be between 90 (final) and 140 (after first transaction)
        for balance in actual_balances:
            assert (
                90 <= balance <= 140
            ), f"Balance {balance} is outside valid range [90, 140]"

        # Final balance (minimum) should always be 90
        assert (
            min(actual_balances) == 90
        ), f"Final balance should be 90, got {min(actual_balances)}"

    finally:
        await cleanup_test_user(user_id)