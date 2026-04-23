def on_test_stop(environment, **_kwargs):
    """Print comprehensive test summary with performance grading."""
    stats = environment.stats.total
    if stats.num_requests == 0:
        return

    # Get percentiles and basic stats
    stats.get_response_time_percentile(0.50) or 0
    p95 = stats.get_response_time_percentile(0.95) or 0
    stats.get_response_time_percentile(0.99) or 0
    fail_ratio = stats.fail_ratio
    getattr(stats, "current_rps", 0.0)

    # Get slow request counts
    _env_bags.get(environment, {"slow_10s": 0, "slow_20s": 0})

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

    # Production readiness assessment
    if grade in ["A", "B"] or grade == "C":
        pass
    else:
        pass

    # Cleanup
    _env_bags.pop(environment, None)