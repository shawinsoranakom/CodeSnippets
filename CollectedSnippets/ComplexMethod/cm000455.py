async def test_prove_database_locking_behavior(server: SpinTestServer):
    """Definitively prove whether database locking causes waiting vs failures."""
    user_id = f"locking-test-{uuid4()}"
    await create_test_user(user_id)

    try:
        # Set balance to exact amount that can handle all spends using internal method (bypasses Stripe)
        await credit_system._add_transaction(
            user_id=user_id,
            amount=60,  # Exactly 10+20+30
            transaction_type=CreditTransactionType.TOP_UP,
            metadata=SafeJson({"test": "exact_amount_test"}),
        )

        async def spend_with_precise_timing(amount: int, label: str):
            request_start = asyncio.get_event_loop().time()
            db_operation_start = asyncio.get_event_loop().time()
            try:
                # Add a small delay to increase chance of true concurrency
                await asyncio.sleep(0.001)

                db_operation_start = asyncio.get_event_loop().time()
                await credit_system.spend_credits(
                    user_id,
                    amount,
                    UsageTransactionMetadata(
                        graph_exec_id=f"locking-{label}",
                        reason=f"Locking test {label}",
                    ),
                )
                db_operation_end = asyncio.get_event_loop().time()

                return {
                    "label": label,
                    "status": "SUCCESS",
                    "request_start": request_start,
                    "db_start": db_operation_start,
                    "db_end": db_operation_end,
                    "db_duration": db_operation_end - db_operation_start,
                }
            except Exception as e:
                db_operation_end = asyncio.get_event_loop().time()
                return {
                    "label": label,
                    "status": "FAILED",
                    "error": str(e),
                    "request_start": request_start,
                    "db_start": db_operation_start,
                    "db_end": db_operation_end,
                    "db_duration": db_operation_end - db_operation_start,
                }

        # Launch all requests simultaneously
        results = await asyncio.gather(
            spend_with_precise_timing(10, "A"),
            spend_with_precise_timing(20, "B"),
            spend_with_precise_timing(30, "C"),
            return_exceptions=True,
        )

        print("\n🔍 LOCKING BEHAVIOR ANALYSIS:")
        print("=" * 50)

        successful = [
            r for r in results if isinstance(r, dict) and r.get("status") == "SUCCESS"
        ]
        failed = [
            r for r in results if isinstance(r, dict) and r.get("status") == "FAILED"
        ]

        print(f"✅ Successful operations: {len(successful)}")
        print(f"❌ Failed operations: {len(failed)}")

        if len(failed) > 0:
            print(
                "\n🚫 CONCURRENT FAILURES - Some requests failed due to insufficient balance:"
            )
            for result in failed:
                if isinstance(result, dict):
                    print(
                        f"   {result['label']}: {result.get('error', 'Unknown error')}"
                    )

        if len(successful) == 3:
            print(
                "\n🔒 SERIALIZATION CONFIRMED - All requests succeeded, indicating they were queued:"
            )

            # Sort by actual execution time to see order
            dict_results = [r for r in results if isinstance(r, dict)]
            sorted_results = sorted(dict_results, key=lambda x: x["db_start"])

            for i, result in enumerate(sorted_results):
                print(
                    f"   {i+1}. {result['label']}: DB operation took {result['db_duration']:.4f}s"
                )

            # Check if any operations overlapped at the database level
            print("\n⏱️  Database operation timeline:")
            for result in sorted_results:
                print(
                    f"   {result['label']}: {result['db_start']:.4f} -> {result['db_end']:.4f}"
                )

        # Verify final state
        final_balance = await credit_system.get_credits(user_id)
        print(f"\n💰 Final balance: {final_balance}")

        if len(successful) == 3:
            assert (
                final_balance == 0
            ), f"If all succeeded, balance should be 0, got {final_balance}"
            print(
                "✅ CONCLUSION: Database row locking causes requests to WAIT and execute serially"
            )
        else:
            print(
                "❌ CONCLUSION: Some requests failed, indicating different concurrency behavior"
            )

    finally:
        await cleanup_test_user(user_id)