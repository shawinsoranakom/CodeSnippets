def spmd_check(gm: torch.fx.GraphModule) -> bool:
    """Verify all ranks have identical FX graph structure (SPMD).

    Computes a structural hash (op targets + tensor metadata including
    shapes, dtypes, strides) and compares across ranks.
    On mismatch, emits a diagnostic report to stdout, logging, and
    trace_structured.

    Returns True if graphs match (SPMD), False on mismatch.
    """
    import torch.distributed as dist

    if not dist.is_initialized() or dist.get_world_size() <= 1:
        return True

    structure_hash = _compute_hash(gm)
    if structure_hash is None:
        return True

    from torch._subclasses.fake_tensor import unset_fake_temporarily
    from torch.distributed.distributed_c10d import _get_default_group

    pg = _get_default_group()
    world_size = dist.get_world_size()
    rank = dist.get_rank()

    with unset_fake_temporarily():
        all_hashes: list[int] = [0] * world_size
        dist.all_gather_object(all_hashes, structure_hash, pg)

    if all(h == all_hashes[0] for h in all_hashes):
        return True

    # Mismatch detected — build and gather diagnostic fingerprints
    fingerprint = _build_diag_fingerprint(gm)
    with unset_fake_temporarily():
        all_fingerprints: list[tuple[object, ...]] = [() for _ in range(world_size)]
        dist.all_gather_object(all_fingerprints, fingerprint, pg)

    report = _build_mismatch_report(all_fingerprints, rank, world_size)

    print(report, flush=True)
    log.warning("\n%s", report)

    trace_structured(
        "artifact",
        metadata_fn=lambda: {
            "name": "inductor_spmd_graph_mismatch",
            "encoding": "string",
        },
        payload_fn=lambda: report,
    )

    if config.aten_distributed_optimizations.spmd_mismatch == "error":
        raise RuntimeError(
            "SPMD graph verification failed. "
            'Set aten_distributed_optimizations.spmd_mismatch="warn" '
            "to warn instead of fail.\n" + report
        )

    return False