def render_delta_scurve(
    deltas: list[ModelDelta],
    metric: Metric,
    term_width: int | None = None,
    term_height: int | None = None,
):
    if not deltas:
        return

    if term_width is None or term_height is None:
        sz = shutil.get_terminal_size((100, 50))
        term_width = term_width or sz.columns
        term_height = term_height or sz.lines

    sorted_deltas = sorted(deltas, key=lambda d: d.delta_pct)
    n = len(sorted_deltas)
    max_rows = max(term_height - 5, 15)
    display = subsample(sorted_deltas, max_rows)
    skipped = n - len(display)

    header = f"Delta S-curve ({n} models)"
    if skipped > 0:
        header += f" [showing {len(display)}/{n}]"
    print(f"\n  {header}")
    print(f"  {'─' * min(len(header), term_width - 4)}")

    max_name = min(max(len(d.name) for d in display), 28)
    # "  name  +12.3%  {bar}"
    prefix_len = 2 + max_name + 2 + 7 + 2
    plot_width = max(term_width - prefix_len - 1, 20)

    # Range: cap at p5/p95 to avoid outlier squishing
    p5_idx = max(0, int(n * 0.05))
    p95_idx = min(n - 1, int(n * 0.95))
    range_lo = min(sorted_deltas[p5_idx].delta_pct, -10)
    range_hi = max(sorted_deltas[p95_idx].delta_pct, 10)
    # Ensure symmetric-ish around 0
    abs_max = max(abs(range_lo), abs(range_hi))
    range_lo = -abs_max
    range_hi = abs_max
    span = range_hi - range_lo
    if span == 0:
        span = 1

    def pct_to_col(pct: float) -> int:
        return max(
            0, min(plot_width - 1, int((pct - range_lo) / span * (plot_width - 1)))
        )

    zero_col = pct_to_col(0)

    for d in display:
        name = d.name[:max_name].ljust(max_name)
        col = pct_to_col(d.delta_pct)
        bar = [" "] * plot_width
        bar[zero_col] = "|"
        if col <= zero_col:
            for i in range(col, zero_col):
                bar[i] = "·"
            bar[zero_col] = "|"
        else:
            bar[zero_col] = "|"
            for i in range(zero_col + 1, col + 1):
                bar[i] = "·"
        print(f"  {name}  {d.delta_pct:>+6.1f}%  {''.join(bar)}")

    pad = " " * prefix_len
    print(f"{pad}{' ' * zero_col}0%")