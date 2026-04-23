def equal_strategy(op_schema: OpSchema) -> StrategyType:
    # equal_strategy deals with ops that comparing two tensor, we need to make sure
    # sharding layout the same with two operands, we choose to follow the arg with max
    # num of shards, still keep is_same_size here for completeness as they share the
    # same strategy in theory.
    mesh = op_schema.get_mesh_from_args()
    self_strategy, other_strategy = op_schema.args_schema
    if not isinstance(self_strategy, OpStrategy):
        raise AssertionError(f"Expected OpStrategy, got {type(self_strategy)}")
    if not isinstance(other_strategy, OpStrategy):
        raise AssertionError(f"Expected OpStrategy, got {type(other_strategy)}")

    # If either tensor is 0-dimensional (scalar), we must use Replicate for both
    if self_strategy.ndim == 0 or other_strategy.ndim == 0:
        replicate_spec = DTensorSpec(
            mesh=mesh,
            placements=tuple(Replicate() for _ in range(mesh.ndim)),
        )
        return OpStrategy([OpSpec(output_specs=replicate_spec)])

    select_strategy = (
        self_strategy
        if self_strategy.max_num_shards() >= other_strategy.max_num_shards()
        else other_strategy
    )
    equal_strategy = OpStrategy([])

    for arg_strategy in select_strategy.strategies:
        arg_spec = arg_strategy.output_spec
        if is_tensor_partial(arg_spec):
            # if the arg_spec have partial, reshard to replicate
            # otherwise local shard tensor comparison would be invalid
            output_spec = DTensorSpec(
                mesh=mesh,
                placements=tuple(
                    Replicate() if isinstance(p, Partial) else p
                    for p in arg_spec.placements
                ),
            )
            equal_strategy.strategies.append(OpSpec(output_specs=output_spec))
        else:
            equal_strategy.strategies.append(OpSpec(arg_spec))
    return equal_strategy