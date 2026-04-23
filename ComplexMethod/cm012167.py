def gather_node_runtime_estimations(
    gm: torch.fx.GraphModule,
    custom_runtime_estimation: Callable[[fx.Node, int | None], float | None]
    | None = None,
    collective_estimator: Literal["analytical", "benchmark"] = "analytical",
    enable_fusion_regions: bool = False,
    log_estimations: bool = False,
) -> tuple[dict[fx.Node, float], dict[fx.Node, Any]]:
    """Gather initial runtime estimations for all nodes without scheduling.

    Uses analytical models (roofline) for compute nodes — the alignment step
    in OverlapScheduler.run() replaces these with benchmarked + cross-rank-aligned
    values. Collectives use bandwidth formulas or CUDA events depending on
    collective_estimator.

    When enable_fusion_regions is True, builds and collapses fusion regions
    (mutating gm's graph), then includes their costs in the estimations.

    Args:
        collective_estimator: "analytical" uses bandwidth formulas,
            "benchmark" uses CUDA events for collectives.
        log_estimations: When True, log compute and collective estimations
            via trace_structured for tlparse.

    Returns (estimations, fusion_region_of) where estimations maps fx.Node to
    runtime in ms, and fusion_region_of maps call_module nodes to FusionRegion
    objects (empty dict if fusion regions are disabled).
    """
    # Build and collapse fusion regions first (mutates gm)
    fusion_region_of: dict[fx.Node, Any] = {}
    if enable_fusion_regions:
        from torch._inductor.fx_passes.fusion_regions import (
            build_fusion_regions,
            collapse_fusion_regions,
        )

        fusion_region_of = build_fusion_regions(gm)
        if fusion_region_of:
            fusion_region_of = collapse_fusion_regions(gm, fusion_region_of)

    estimations: dict[fx.Node, float] = {}
    nodes = list(gm.graph.nodes)

    # Collectives
    collective_nodes: list[fx.Node] = []
    for node in nodes:
        if _schedulable_wait_node(node):
            start = _get_collective_node_from_wait(node)
            assert start is not None
            if start in estimations:
                continue
            estimations[start] = estimate_collective_time(
                start,
                custom_runtime_estimation=custom_runtime_estimation,
                collective_estimator=collective_estimator,
            )
            collective_nodes.append(start)

    # Compute nodes (matmul, bmm, etc.) — analytical estimates only.
    # The alignment step in run() replaces these with benchmarked + aligned values.
    compute_nodes: list[fx.Node] = []
    compute_analytical: list[float] = []

    for node in nodes:
        if is_compute_node(node):
            est = estimate_roofline_runtime_ms(node)
            if custom_runtime_estimation is not None:
                custom_est = custom_runtime_estimation(node, None)
                if custom_est is not None:
                    est = custom_est
            estimations[node] = est
            compute_nodes.append(node)
            compute_analytical.append(est)
        elif node.op == "call_function" and node not in estimations:
            if custom_runtime_estimation is not None:
                est = custom_runtime_estimation(node, None)
                if est is not None:
                    estimations[node] = est
            else:
                est = estimate_roofline_runtime_ms(node)
                if est > 0:
                    estimations[node] = est

    # Fusion region costs (call_module nodes from collapse_fusion_regions)
    for node, region in fusion_region_of.items():
        estimations[node] = region.cost_ms  # pyrefly: ignore[missing-attribute]

    # Logging
    if log_estimations and compute_nodes:
        from torch._inductor.fx_passes.node_runtime_estimation import (
            _log_compute_estimations,
        )

        _log_compute_estimations(
            compute_nodes,
            compute_analytical,
            compute_analytical,
        )

    if log_estimations and collective_nodes:
        from torch._inductor.fx_passes.node_runtime_estimation import (
            _log_collective_benchmarks,
        )

        _log_collective_benchmarks(
            collective_nodes,
            artifact_name="fx_collectives_analytical_estimation",
        )

    return estimations, fusion_region_of