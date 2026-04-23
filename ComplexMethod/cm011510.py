def index_single_dim_strategy(
    op: OpOverload, args_schema: ArgsType, kwargs_schema: KwargsType
) -> list[list[Placement | _ShardingPlaceholder]]:
    values_meta, multi_indices_meta = args_schema
    if not isinstance(values_meta, TensorMeta):
        raise AssertionError(f"Expected TensorMeta, got {type(values_meta)}")
    if not isinstance(multi_indices_meta, (list, tuple)):
        raise AssertionError(f"Expected list or tuple, got {type(multi_indices_meta)}")

    indexed_dims = [i for i, idx in enumerate(multi_indices_meta) if idx is not None]
    non_indexed_dims = [
        i for i in range(len(values_meta.shape)) if i not in set(indexed_dims)
    ]

    index_metas = [idx for idx in multi_indices_meta if idx is not None]
    if not all(isinstance(m, TensorMeta) for m in index_metas):
        raise AssertionError("Expected all index metas to be TensorMeta")
    broadcast_ndim = max(len(m.shape) for m in index_metas)
    num_indices = len(indexed_dims)

    # Determine where index output dims are inserted in the result
    all_consecutive = all(
        indexed_dims[i + 1] - indexed_dims[i] == 1 for i in range(len(indexed_dims) - 1)
    )
    insert_dim = indexed_dims[0] if all_consecutive else 0

    def values_dim_to_output_dim(d: int) -> int:
        if d < insert_dim:
            return d
        return d + broadcast_ndim - sum(1 for idx_dim in indexed_dims if d > idx_dim)

    strategies: list[list[Placement | _ShardingPlaceholder]] = []

    # Shard values on a non-indexed dim, all indices replicated
    for d in non_indexed_dims:
        out_dim = values_dim_to_output_dim(d)
        rule: list[Placement | _ShardingPlaceholder] = [_ShardingPlaceholder(out_dim)]
        rule.append(_ShardingPlaceholder(d))
        rule.extend([Replicate()] * num_indices)
        strategies.append(rule)

    # Shard indices on the same broadcast dim.  Each index tensor may
    # have a different ndim, so we map broadcast dim → tensor dim via
    # left-padding.  Tensors with size 1 on that dim are replicated
    # (broadcast semantics).
    for bd in range(broadcast_ndim):
        per_tensor: list[tuple[int, int]] = []  # (tensor_dim, size)
        for m in index_metas:
            offset = broadcast_ndim - len(m.shape)
            if bd < offset:
                per_tensor.append((-1, 1))  # implicit broadcast
            else:
                td = bd - offset
                per_tensor.append((td, m.shape[td]))
        if all(s == 1 for _, s in per_tensor):
            continue  # all broadcast-only, skip
        out_dim = bd + insert_dim
        rule: list[Placement | _ShardingPlaceholder] = [_ShardingPlaceholder(out_dim)]
        rule.append(Replicate())
        for td, s in per_tensor:
            if s > 1:
                rule.append(_ShardingPlaceholder(td))
            else:
                rule.append(Replicate())
        strategies.append(rule)

    # Partial passthrough from values
    for reduce_op in Partial.LINEAR_REDUCE_OPS:
        rule: list[Placement | _ShardingPlaceholder] = [
            Partial(reduce_op),
            Partial(reduce_op),
        ]
        rule.extend([Replicate()] * num_indices)
        strategies.append(rule)

    return strategies