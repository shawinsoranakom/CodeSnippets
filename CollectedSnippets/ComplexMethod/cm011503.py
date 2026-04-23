def gen_slice_strategy(op_schema: OpSchema) -> StrategyType:
    """Forward all shardings except the slice dimension."""
    defaults = (None, 0, None, None, 1)
    input_strategy, dim, start, end, step = (
        op_schema.args_schema + defaults[len(op_schema.args_schema) :]
    )
    if not isinstance(input_strategy, OpStrategy):
        raise AssertionError(f"Expected OpStrategy, got {type(input_strategy)}")

    mesh = input_strategy.mesh
    input_shape = input_strategy.shape
    input_ndim = input_strategy.ndim
    if not isinstance(dim, int):
        raise AssertionError(f"Expected int, got {type(dim)}")
    if start is None:
        start = 0
    if end is None or statically_known_true(end > input_shape[dim]):
        end = input_shape[dim]
    if not isinstance(start, IntLike):
        raise AssertionError(f"Expected IntLike, got {type(start)}")
    if not isinstance(end, IntLike):
        raise AssertionError(f"Expected IntLike, got {type(end)}")
    if not isinstance(step, IntLike):
        raise AssertionError(f"Expected IntLike, got {type(step)}")

    # normalize args
    slice_dim = normalize_dim(dim, input_ndim)  # type: ignore[arg-type]
    start = normalize_dim(start, input_shape[dim])  # type: ignore[arg-type]
    end = normalize_dim(end, input_shape[dim])  # type: ignore[arg-type]

    statically_redundant_slice = (
        statically_known_true(start == 0)
        and statically_known_true(end == input_shape[dim])
        and statically_known_true(step == 1)
    )

    slice_strategy = OpStrategy([])

    for arg_strategy in input_strategy.strategies:
        arg_spec = arg_strategy.output_spec
        if (
            not is_tensor_dim_sharded(arg_spec, dim=slice_dim)
            or statically_redundant_slice
        ):
            # only add the strategy if the slice dim is not sharded
            out_spec = DTensorSpec(mesh, arg_spec.placements)
            slice_strategy.strategies.append(
                OpSpec(
                    output_specs=out_spec,
                    input_specs=(arg_spec,),
                    redistribute_cost=[[0.0] * len(input_strategy.strategies)],
                )
            )
    if not slice_strategy.strategies:
        # if all strategies are filtered out, unsharding all specs on slice dim
        # of the input strategy, and use that as the op strategy
        for arg_strategy in input_strategy.strategies:
            arg_spec = arg_strategy.output_spec
            unshard_spec = DTensorSpec(
                mesh, unshard_tensor_dim(arg_spec.placements, dim=slice_dim)
            )
            slice_strategy.strategies.append(
                OpSpec(
                    output_specs=unshard_spec,
                    redistribute_cost=[
                        generate_redistribute_costs(input_strategy, unshard_spec)
                    ],
                )
            )
    return slice_strategy