def print_regressions(deltas: list[ModelDelta], metric: Metric, top_n: int):
    # For higher_is_better metrics, regression = negative delta
    # For lower_is_better metrics, regression = positive delta
    if metric.higher_is_better:
        bad = [d for d in deltas if d.delta_pct < -RELATIVE_THRESHOLD * 100]
        bad.sort(key=lambda d: d.delta_pct)
    else:
        bad = [d for d in deltas if d.delta_pct > RELATIVE_THRESHOLD * 100]
        bad.sort(key=lambda d: d.delta_pct, reverse=True)

    if not bad:
        print(f"\n  No regressions (>{RELATIVE_THRESHOLD * 100:.0f}% change).")
        return

    print(f"\n  Regressions ({len(bad)} models, showing top {min(top_n, len(bad))}):")
    for i, d in enumerate(bad[:top_n], 1):
        print(
            f"    {i}. {d.name:<30}  "
            f"{d.base_val:.2f}{metric.unit} → {d.head_val:.2f}{metric.unit}  "
            f"{d.delta_pct:>+6.1f}%  {d.short_config}"
        )