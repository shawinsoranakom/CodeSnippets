def _log_collective_benchmarks(
    collective_nodes: list[fx.Node],
    collective_keys: list[str] | None = None,
    benchmarked_medians: list[float] | None = None,
    world_size: int | None = None,
    artifact_name: str = "fx_collectives_analytical_estimation",
) -> None:
    """Log collective estimations for tlparse. Includes benchmarks if provided."""
    if world_size is None:
        world_size = (
            torch.distributed.get_world_size()
            if torch.distributed.is_initialized()
            else 1
        )

    has_benchmarks = benchmarked_medians is not None

    if has_benchmarks:
        headers = [
            "Collective Key",
            "Benchmarked(ms)",
            "NCCL Est(ms)",
            "Inductor Est(ms)",
            "NCCL Diff(ratio)",
            "Inductor Diff(ratio)",
        ]
    else:
        headers = [
            "Collective Key",
            "NCCL Est(ms)",
            "Inductor Est(ms)",
        ]

    rows = []
    for i, coll_node in enumerate(collective_nodes):
        key = collective_keys[i] if collective_keys else _get_collective_key(coll_node)
        nccl_ms, inductor_ms = _get_collective_estimations(coll_node)

        if benchmarked_medians is not None:
            benchmarked_ms = benchmarked_medians[i]
            nccl_diff_pct = (nccl_ms / benchmarked_ms) if benchmarked_ms > 0 else 0
            inductor_diff_pct = (
                (inductor_ms / benchmarked_ms) if benchmarked_ms > 0 else 0
            )
            rows.append(
                [
                    key,
                    f"{benchmarked_ms:.4f}",
                    f"{nccl_ms:.4f}",
                    f"{inductor_ms:.4f}",
                    f"{nccl_diff_pct:.2f}",
                    f"{inductor_diff_pct:.2f}",
                ]
            )
        else:
            rows.append(
                [
                    key,
                    f"{nccl_ms:.4f}",
                    f"{inductor_ms:.4f}",
                ]
            )

    log_str = f"# World size: {world_size}\n"
    log_str += _format_csv(headers, rows)

    trace_structured(
        "artifact",
        metadata_fn=lambda: {
            "name": artifact_name,
            "encoding": "string",
        },
        payload_fn=lambda: log_str,
    )