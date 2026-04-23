def compute_deltas(
    head_perf: list[PerfData], base_perf: list[PerfData], metric: Metric
) -> tuple[list[ModelDelta], dict[str, ConfigAgg]]:
    """Join head and base on (device, config, model_name) and compute deltas.

    Returns (per_model_deltas, per_config_aggregates).
    per_config_aggregates maps qualified_config -> ConfigAgg.
    """
    # Build base lookup: (device, config, model_name) -> metric value
    base_lookup: dict[tuple[str, str, str], float] = {}
    for perf in base_perf:
        for m in perf.models:
            v = getattr(m, metric.field)
            if v > 0:
                base_lookup[(perf.device, perf.config, m.name)] = v

    deltas = []
    for perf in head_perf:
        for m in perf.models:
            head_val = getattr(m, metric.field)
            if head_val <= 0:
                continue
            key = (perf.device, perf.config, m.name)
            if key not in base_lookup:
                continue
            base_val = base_lookup[key]
            deltas.append(
                ModelDelta(
                    name=m.name,
                    base_val=base_val,
                    head_val=head_val,
                    config=perf.config,
                    device=perf.device,
                )
            )

    # Group deltas by qualified_config for paired aggregates
    deltas_by_qconfig: dict[str, list[ModelDelta]] = defaultdict(list)
    for d in deltas:
        qc = f"{d.device}/{d.config}" if d.device else d.config
        deltas_by_qconfig[qc].append(d)

    # Per-config aggregates (keyed by qualified_config for display)
    config_aggs: dict[str, ConfigAgg] = {}
    base_by_qconfig: dict[str, PerfData] = {p.qualified_config: p for p in base_perf}
    for perf in head_perf:
        qc = perf.qualified_config
        if qc not in base_by_qconfig:
            continue
        base_perf_data = base_by_qconfig[qc]
        head_agg = perf.aggregate_metric(metric)
        base_agg = base_perf_data.aggregate_metric(metric)
        head_count = len([m for m in perf.models if getattr(m, metric.field) > 0])
        base_count = len(
            [m for m in base_perf_data.models if getattr(m, metric.field) > 0]
        )

        paired = deltas_by_qconfig.get(qc, [])
        ratios = [d.head_val / d.base_val for d in paired if d.base_val > 0]
        config_aggs[qc] = ConfigAgg(
            base_agg=base_agg,
            base_count=base_count,
            head_agg=head_agg,
            head_count=head_count,
            paired_ratio=gmean(ratios) if ratios else 0.0,
            paired_count=len(ratios),
        )

    return deltas, config_aggs