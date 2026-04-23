async def compare_counts(before, after):
    """Compare counts before and after refresh."""
    print("\n5. Comparing counts before and after refresh...")
    print("-" * 40)

    # Compare agent runs
    print("🔍 Agent run changes:")
    before_runs = before["agent_runs"].get("total_runs") or 0
    after_runs = after["agent_runs"].get("total_runs") or 0
    print(
        f"   Total runs: {before_runs} → {after_runs} " f"(+{after_runs - before_runs})"
    )

    # Compare reviews
    print("\n🔍 Review changes:")
    before_reviews = before["reviews"].get("total_reviews") or 0
    after_reviews = after["reviews"].get("total_reviews") or 0
    print(
        f"   Total reviews: {before_reviews} → {after_reviews} "
        f"(+{after_reviews - before_reviews})"
    )

    # Compare store agents
    print("\n🔍 StoreAgent view changes:")
    before_avg_runs = before["store_agents"].get("avg_runs", 0) or 0
    after_avg_runs = after["store_agents"].get("avg_runs", 0) or 0
    print(
        f"   Average runs: {before_avg_runs:.2f} → {after_avg_runs:.2f} "
        f"(+{after_avg_runs - before_avg_runs:.2f})"
    )

    # Verify changes occurred
    runs_changed = (after["agent_runs"].get("total_runs") or 0) > (
        before["agent_runs"].get("total_runs") or 0
    )
    reviews_changed = (after["reviews"].get("total_reviews") or 0) > (
        before["reviews"].get("total_reviews") or 0
    )

    if runs_changed and reviews_changed:
        print("\n✅ Materialized views are updating correctly!")
        return True
    else:
        print("\n⚠️  Some materialized views may not have updated:")
        if not runs_changed:
            print("   - Agent run counts did not increase")
        if not reviews_changed:
            print("   - Review counts did not increase")
        return False