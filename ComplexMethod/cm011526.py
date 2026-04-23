def query_single_dim_strategy(
    op_overload: OpOverload,
    captured_args: tuple[Any, ...],
    captured_kwargs: dict[str, Any],
) -> list[list[Placement]] | None:
    """
    Query DTensor's single-dim strategy for given input tensors.
    Returns list of [output_placement, *input_placements] rules.
    """
    propagator = DTensor._op_dispatcher.sharding_propagator

    if op_overload not in propagator.op_single_dim_strategy_funcs:
        return None

    strategy_func = propagator.op_single_dim_strategy_funcs[op_overload]

    args_meta = tuple(
        TensorMeta(shape=a.shape, stride=a.stride(), dtype=a.dtype)
        if isinstance(a, torch.Tensor)
        else a
        for a in captured_args
    )
    kwargs_meta = {
        k: TensorMeta(shape=v.shape, stride=v.stride(), dtype=v.dtype)
        if isinstance(v, torch.Tensor)
        else v
        for k, v in captured_kwargs.items()
    }

    try:
        result = strategy_func(op_overload, args_meta, kwargs_meta)

        expanded_result: list[list[Placement]] = []
        for combo in result:
            expanded_combo: list[Placement] = []
            for p in combo:
                if isinstance(p, _ShardingPlaceholder):
                    expanded_combo.append(Shard(p.dim))
                else:
                    expanded_combo.append(p)
            expanded_result.append(expanded_combo)

        return expanded_result
    except Exception:
        return None