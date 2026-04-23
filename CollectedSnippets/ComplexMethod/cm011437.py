def _gen_transform_infos_non_cached(
    src_spec: DTensorSpec,
    dst_spec: DTensorSpec,
    use_graph_based_transform: bool | None = None,
) -> list[_TransformInfo]:
    device_mesh = src_spec.device_mesh
    src_shard_order = src_spec.shard_order
    dst_shard_order = dst_spec.shard_order
    # DTensorSpec should automatically generate shard_order, and it can be () if
    # no shard.
    has_non_default_order = not all(
        DTensorSpec.is_default_device_order(order)
        for order in (src_shard_order, dst_shard_order)
    )
    has_strided_shard = any(
        isinstance(p, _StridedShard)
        for p in (*src_spec.placements, *dst_spec.placements)
    )

    # Determine which transform strategy to use:
    # 1. Non-standard device order or contains _StridedShard → always use graph-based
    # 2. Global flag or explicit parameter True → use graph-based
    # 3. Otherwise → use greedy
    if has_non_default_order or has_strided_shard:
        use_graph_based_transform = True
    elif _FORCE_MIN_COST_REDISTRIBUTION_PLAN is not None:
        use_graph_based_transform = _FORCE_MIN_COST_REDISTRIBUTION_PLAN
    elif use_graph_based_transform is None:
        use_graph_based_transform = False
    if src_spec.tensor_meta is None:
        raise AssertionError
    drp = get_redistribute_planner(
        device_mesh,
        src_spec.tensor_meta,
    )
    if use_graph_based_transform:
        # TODO(zpcore): Temporary workaround for the case where _StridedShard
        # cannot be decoded into shard order. This happens when
        # use_strided_shard_as_shard_order defaults to True (e.g. in
        # Redistribute.forward where the target DTensorSpec is constructed from
        # raw placements without the flag), but the split_factor doesn't
        # correspond to any valid product of mesh dimension sizes (e.g. sf=2
        # on a 1D mesh). A proper fix is to either pass
        # use_strided_shard_as_shard_order through the Redistribute API, or
        # migrate to explicit shard_order so _StridedShard is no longer
        # overloaded for two purposes.
        try:
            transform_infos = drp.generate_graph_based_transform_infos(
                src_spec, dst_spec, src_spec.shape
            )
        except _StridedShardNotDecodableError:
            transform_infos = drp.generate_greedy_transform_infos(src_spec, dst_spec)
    else:
        transform_infos = drp.generate_greedy_transform_infos(src_spec, dst_spec)
    return transform_infos