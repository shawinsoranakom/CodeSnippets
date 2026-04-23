def render_scurve(
    perf: PerfData,
    metric: Metric,
    top_n: int = 5,
    term_width: int | None = None,
    term_height: int | None = None,
):
    if not perf.models:
        return

    if term_width is None or term_height is None:
        sz = shutil.get_terminal_size((100, 50))
        term_width = term_width or sz.columns
        term_height = term_height or sz.lines

    live = [m for m in perf.models if getattr(m, metric.field) > 0]
    if not live:
        return

    sorted_models = sorted(live, key=lambda m: getattr(m, metric.field))
    agg = perf.aggregate_metric(metric)
    n = len(sorted_models)

    # Reserve lines for header (2) + axis label (1) + padding (2)
    max_rows = max(term_height - 5, 15)
    display = subsample(sorted_models, max_rows)
    skipped = n - len(display)

    agg_label = metric.aggregate
    header = f"{perf.config} ({n} data points, {agg_label}={agg:.2f}{metric.unit})"
    if skipped > 0:
        header += f" [showing {len(display)}/{n}]"
    print(f"\n  {header}")
    print(f"  {'─' * min(len(header), term_width - 4)}")

    def fmt_val(v: float) -> str:
        if metric.unit == "s" or metric.unit == "ms":
            return f"{v:7.1f}{metric.unit}"
        return f"{v:5.2f}{metric.unit}"

    # Layout: "  {name:<max_name}  {val:>8}  {dots}"
    sample_val = fmt_val(display[0] and getattr(display[0], metric.field))
    max_name = min(max(len(m.name) for m in display), 30)
    val_width = len(sample_val)
    prefix_len = 2 + max_name + 2 + val_width + 2
    plot_width = max(term_width - prefix_len - 1, 20)

    def get_val(m):
        return getattr(m, metric.field)

    min_val = get_val(sorted_models[0])
    p95_idx = max(0, int(n * 0.95) - 1)
    p95_val = get_val(sorted_models[p95_idx])

    # For ratio metrics (speedup, compression_ratio), anchor at 1.0
    # For absolute metrics (latency), anchor at 0
    if metric.unit == "x":
        plot_min = min(min_val, 0.5)
        plot_max = max(p95_val * 1.1, 1.5)
        marker_val = 1.0
        marker_label = "1.0x"
    else:
        plot_min = 0
        plot_max = p95_val * 1.1
        marker_val = None
        marker_label = None

    span = plot_max - plot_min
    if span == 0:
        span = 1

    def val_to_col(v: float) -> int:
        return max(
            0, min(plot_width - 1, int((v - plot_min) / span * (plot_width - 1)))
        )

    marker_col = val_to_col(marker_val) if marker_val is not None else None

    for m in display:
        name = m.name[:max_name].ljust(max_name)
        v = get_val(m)
        col = val_to_col(v)
        bar = [" "] * plot_width
        if marker_col is not None:
            bar[marker_col] = "|"
        for i in range(col + 1):
            if marker_col is not None and i == marker_col:
                bar[i] = "|"
            else:
                bar[i] = "·"
        print(f"  {name}  {fmt_val(v)}  {''.join(bar)}")

    pad = " " * prefix_len
    if marker_label and marker_col is not None:
        print(f"{pad}{' ' * marker_col}{marker_label}")
    else:
        print()