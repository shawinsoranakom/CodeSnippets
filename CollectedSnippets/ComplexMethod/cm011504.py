def gen_slice_scatter_strategy(op_schema: OpSchema) -> StrategyType:
    # 1. number of dimensions in input and src need to match.
    # 2. number of elements on all non-dim need to match between input and src.
    # 3. number of elements in src in dim need to match the slice size.
    # Given the above:
    # - We suggest for src to follow the sharding of input, except on the scatter dimension,
    #   where our best bet for now is to make them replicated as a fall-back.
    #   TODO: Ideally we'd like to make sure the output is re-sharded afterwards to keep input sharding.
    mesh = op_schema.get_mesh_from_args()
    input_strategy = op_schema.args_schema[0]
    src_strategy = op_schema.args_schema[1]
    if not isinstance(input_strategy, OpStrategy):
        raise AssertionError(f"Expected OpStrategy, got {type(input_strategy)}")
    if not isinstance(src_strategy, OpStrategy):
        raise AssertionError(f"Expected OpStrategy, got {type(src_strategy)}")
    input_ndim = input_strategy.ndim
    slice_dim = (
        cast(int, op_schema.args_schema[2]) if len(op_schema.args_schema) > 2 else 0
    )
    slice_dim = normalize_dim(slice_dim, input_ndim)

    slice_scatter_strategy = OpStrategy([])
    # by default follow the input strategy for both input and src
    for arg_strategy in input_strategy.strategies:
        arg_spec = arg_strategy.output_spec
        if not (
            is_tensor_dim_sharded(arg_spec, dim=slice_dim)
            or is_tensor_partial(arg_spec)
        ):
            input_spec = DTensorSpec(mesh, arg_spec.placements, arg_spec.tensor_meta)
            # TODO: need to relax the constraint to src
            src_spec = DTensorSpec(mesh, arg_spec.placements)
            # only add the strategy if the slice_scatter dim is not sharded or partial
            slice_scatter_strategy.strategies.append(
                OpSpec(
                    output_specs=arg_spec,
                    input_specs=(input_spec, src_spec),
                    redistribute_cost=[
                        generate_redistribute_costs(input_strategy, input_spec),
                        generate_redistribute_costs(src_strategy, src_spec),
                    ],
                )
            )

    if not slice_scatter_strategy.strategies:
        # if all strategies are filtered out, replicating all specs on slice_scatter dim
        # of the input strategy, and use that as the op strategy
        for arg_strategy in input_strategy.strategies:
            arg_spec = arg_strategy.output_spec
            new_placement = replicate_tensor_dim(arg_spec.placements, dim=slice_dim)
            input_spec = DTensorSpec(mesh, new_placement)
            src_spec = DTensorSpec(mesh, new_placement)
            slice_scatter_strategy.strategies.append(
                OpSpec(
                    output_specs=input_spec,
                    input_specs=(input_spec, src_spec),
                    redistribute_cost=[
                        generate_redistribute_costs(input_strategy, input_spec),
                        generate_redistribute_costs(src_strategy, src_spec),
                    ],
                )
            )
    return slice_scatter_strategy