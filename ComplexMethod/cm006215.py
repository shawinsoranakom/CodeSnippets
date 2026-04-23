def on_test_stop(environment, **_kwargs):
    """Print comprehensive test summary with performance grading."""
    stats = environment.stats.total
    if stats.num_requests == 0:
        return

    # Get percentiles and basic stats
    p50 = stats.get_response_time_percentile(0.50) or 0
    p95 = stats.get_response_time_percentile(0.95) or 0
    p99 = stats.get_response_time_percentile(0.99) or 0
    fail_ratio = stats.fail_ratio
    current_rps = getattr(stats, "current_rps", 0.0)

    # Get slow request counts
    bag = _env_bags.get(environment, {"slow_10s": 0, "slow_20s": 0})

    # Performance grading based on production criteria
    grade = "A"
    issues = []

    if fail_ratio > 0.01:
        grade = "B"
        issues.append(f"fail {fail_ratio:.1%}")
    if fail_ratio > 0.05:
        grade = "C"
    if p95 > 10_000:
        grade = max(grade, "D")
        issues.append(f"p95 {p95 / 1000:.1f}s")
    if p95 > 20_000:
        grade = "F"
        issues.append(f"p95 {p95 / 1000:.1f}s")

    print(f"\n{'=' * 60}")
    print(f"LANGFLOW API LOAD TEST RESULTS - GRADE: {grade}")
    print(f"{'=' * 60}")
    print(f"Requests: {stats.num_requests:,} | Failures: {stats.num_failures:,} ({fail_ratio:.1%})")
    print(f"Response Times: p50={p50 / 1000:.2f}s p95={p95 / 1000:.2f}s p99={p99 / 1000:.2f}s")
    print(f"RPS: {current_rps:.1f} | Slow requests: >10s={bag['slow_10s']} >20s={bag['slow_20s']}")

    if issues:
        print(f"Issues: {', '.join(issues)}")

    # Production readiness assessment
    if grade in ["A", "B"]:
        print("✅ PRODUCTION READY - Performance meets production standards")
    elif grade == "C":
        print("⚠️  CAUTION - Acceptable but monitor closely in production")
    else:
        print("❌ NOT PRODUCTION READY - Significant performance issues detected")

    print(f"{'=' * 60}\n")

    # Save detailed error information
    save_error_summary()

    # Capture Langflow logs
    capture_langflow_logs()

    # Set exit code for CI/CD
    if fail_ratio > 0.01:
        environment.process_exit_code = 1

    # Cleanup
    _env_bags.pop(environment, None)