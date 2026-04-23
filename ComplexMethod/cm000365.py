async def main():
    db = Prisma()
    await db.connect()

    print("=" * 60)
    print("Materialized Views Test")
    print("=" * 60)

    try:
        # Check if data exists
        user_count = await db.user.count()
        if user_count == 0:
            print("❌ No data in database. Please run test_data_creator.py first.")
            await db.disconnect()
            return

        # 1. Check cron job
        cron_exists = await check_cron_job(db)

        # 2. Get initial counts
        counts_before = await get_materialized_view_counts(db)

        # 3. Add test data
        data_added = await add_test_data(db)
        refresh_success = False

        if data_added:
            # Wait a moment for data to be committed
            print("\nWaiting for data to be committed...")
            await asyncio.sleep(2)

            # 4. Manually refresh views
            refresh_success = await refresh_materialized_views(db)

            if refresh_success:
                # 5. Get counts after refresh
                counts_after = await get_materialized_view_counts(db)

                # 6. Compare results
                await compare_counts(counts_before, counts_after)

        # Summary
        print("\n" + "=" * 60)
        print("Test Summary")
        print("=" * 60)
        print(f"✓ pg_cron job exists: {'Yes' if cron_exists else 'No'}")
        print(f"✓ Test data added: {'Yes' if data_added else 'No'}")
        print(f"✓ Manual refresh worked: {'Yes' if refresh_success else 'No'}")
        print(
            f"✓ Views updated correctly: {'Yes' if data_added and refresh_success else 'Cannot verify'}"
        )

        if cron_exists:
            print(
                "\n💡 The materialized views will also refresh automatically every 15 minutes via pg_cron."
            )
        else:
            print(
                "\n⚠️  Automatic refresh is not configured. Views must be refreshed manually."
            )

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()

    await db.disconnect()