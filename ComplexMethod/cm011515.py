def dim_reduction_with_indices_strategy(
    op: torch._ops.OpOverload,
    args_schema: tuple[Any, ...],
    kwargs_schema: dict[str, Any],
) -> list[list[Placement | _ShardingPlaceholder]]:
    input_meta = args_schema[0]
    if not isinstance(input_meta, TensorMeta):
        raise AssertionError(f"Expected TensorMeta, got {type(input_meta)}")

    ndim = len(input_meta.shape)
    dim = normalize_dim(cast(int, args_schema[1]) if len(args_schema) > 1 else -1, ndim)
    keep_dim = len(args_schema) > 2 and bool(args_schema[2])

    strategies: list[list[Placement | _ShardingPlaceholder]] = []
    for d in range(ndim):
        if d == dim:
            continue
        out_d = d if keep_dim or d < dim else d - 1
        strategies.append(
            [
                _ShardingPlaceholder(out_d),
                _ShardingPlaceholder(out_d),
                _ShardingPlaceholder(d),
            ]
        )
    return strategies