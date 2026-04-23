def diagonal_scatter_single_dim_strategy(
    op: OpOverload,
    args_schema: ArgsType,
    kwargs_schema: KwargsType,
) -> list[list[Placement | _ShardingPlaceholder]]:
    input_meta = args_schema[0]
    if not isinstance(input_meta, TensorMeta):
        raise AssertionError(f"Expected TensorMeta, got {type(input_meta)}")
    ndim = len(input_meta.shape)
    # schema: (self, src, offset=0, dim1=0, dim2=1)
    dim1 = cast(int, args_schema[3]) if len(args_schema) > 3 else 0
    dim2 = cast(int, args_schema[4]) if len(args_schema) > 4 else 1
    dim1 = normalize_dim(dim1, ndim)
    dim2 = normalize_dim(dim2, ndim)
    min_d, max_d = min(dim1, dim2), max(dim1, dim2)
    # [output, self, src] — src has dim1/dim2 removed and diagonal appended
    strategies: list[list[Placement | _ShardingPlaceholder]] = []
    for d in range(ndim):
        if d in (dim1, dim2):
            continue
        removed = (1 if d > min_d else 0) + (1 if d > max_d else 0)
        strategies.append(
            [
                _ShardingPlaceholder(d),
                _ShardingPlaceholder(d),
                _ShardingPlaceholder(d - removed),
            ]
        )
    return strategies