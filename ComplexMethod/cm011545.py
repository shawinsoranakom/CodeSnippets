def constant_pad_nd_single_dim_strategy(
    op: OpOverload, args_schema: ArgsType, kwargs_schema: KwargsType
) -> list[list[Placement | _ShardingPlaceholder]]:
    # Allow sharding on non-padded dimensions; ban sharding on dims
    # that have non-zero padding (where the pad value must be inserted).
    input_meta = args_schema[0]
    if not isinstance(input_meta, TensorMeta):
        raise AssertionError(f"Expected TensorMeta, got {type(input_meta)}")
    ndim = len(input_meta.shape)
    pad = args_schema[1]
    if not isinstance(pad, (list, tuple)):
        raise AssertionError(f"Expected list or tuple, got {type(pad)}")

    # pad is [dim_{n-1}_left, dim_{n-1}_right, dim_{n-2}_left, ...] from
    # the last dim backwards. Determine which dims have non-zero padding.
    padded_dims = set()
    for i in range(len(pad) // 2):
        if not (
            guard_or_false(pad[i * 2] == 0) and guard_or_false(pad[i * 2 + 1] == 0)
        ):
            padded_dims.add(ndim - 1 - i)

    # Shard on any non-padded dim: output and input share the same placement.
    # All-Replicate is added automatically by the framework.
    strategies: list[list[Placement | _ShardingPlaceholder]] = []
    for dim in range(ndim):
        if dim not in padded_dims:
            strategies.append([_ShardingPlaceholder(dim), _ShardingPlaceholder(dim)])

    # Partial rules: at padded positions every rank writes the same constant v,
    # so reduce(v, v, ..., v) = v for avg/max/min (idempotent). P(sum) only
    # works when v=0 since sum(v, ..., v) = N*v != v otherwise.
    # When all pad amounts are zero the op is a no-op, so all reduce ops hold.
    value = args_schema[2] if len(args_schema) > 2 else 0
    no_padding = all(guard_or_false(pad[i] == 0) for i in range(len(pad)))
    if no_padding or guard_or_false(value == 0):
        reduce_ops = ("sum", "avg", "max", "min")
    else:
        reduce_ops = ("avg", "max", "min")
    for reduce_op in reduce_ops:
        strategies.append([Partial(reduce_op), Partial(reduce_op)])

    return strategies