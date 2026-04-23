def replace_collectives_with_low_contention(
    graph: torch.fx.Graph,
) -> None:
    """Replace FSDP collectives with copy-engine symm_mem variants."""
    symm_mem = torch.ops.symm_mem

    collectives = []
    groups: OrderedSet[str] = OrderedSet()
    for node in list(graph.nodes):
        info = _get_collective_info(node)
        if info is None:
            continue
        is_ag, group_name = info
        collectives.append((node, is_ag, group_name))
        groups.add(group_name)

    if not collectives:
        return

    # Some group names can't be resolved at compile time — skip them.
    valid_groups: OrderedSet[str] = OrderedSet()
    for group_name in groups:
        if _enable_symm_mem(group_name):
            valid_groups.add(group_name)

    # Filter to collectives whose groups we can actually resolve
    collectives = [
        (node, is_ag, gn) for node, is_ag, gn in collectives if gn in valid_groups
    ]
    if not collectives:
        return

    from torch._inductor import config

    min_bytes = config.aten_distributed_optimizations.low_contention_min_bytes_per_rank

    node_positions = {n: i for i, n in enumerate(graph.nodes)}

    replacements = 0
    skipped_small = 0
    skipped_no_overlap = 0
    skipped_nvlink_contention = 0
    for node, is_ag, group_name in collectives:
        coll_type = "AG" if is_ag else "RS"

        # Size filter: LC barrier overhead dominates for small messages
        if min_bytes > 0:
            per_rank_bytes = _get_per_rank_bytes(node, is_ag)
            if per_rank_bytes is not None and per_rank_bytes < min_bytes:
                skipped_small += 1
                log.debug(
                    "LC skip %s %s: size %d < min_bytes %d",
                    coll_type,
                    node.name,
                    per_rank_bytes,
                    min_bytes,
                )
                continue

        # Skip collectives with no compute to hide behind
        if not _has_compute_bound_overlap(node, graph, node_positions):
            skipped_no_overlap += 1
            log.debug("LC skip %s %s: no compute-bound overlap", coll_type, node.name)
            continue

        # Skip if other groups' NCCL collectives overlap on NVLink
        if _has_other_group_collectives(node, group_name, graph, node_positions):
            skipped_nvlink_contention += 1
            log.debug(
                "LC skip %s %s: overlaps other-group collectives (NVLink contention)",
                coll_type,
                node.name,
            )
            continue

        _replace_collective(node, graph, symm_mem, is_ag, group_name)
        replacements += 1

    log.info(
        "Replaced %d/%d FSDP collectives "
        "(skipped_small=%d, skipped_no_overlap=%d, "
        "skipped_nvlink_contention=%d, min_bytes=%d)",
        replacements,
        len(collectives),
        skipped_small,
        skipped_no_overlap,
        skipped_nvlink_contention,
        min_bytes,
    )