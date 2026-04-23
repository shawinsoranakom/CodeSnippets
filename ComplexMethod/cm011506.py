def scatter_add_strategy(op_schema: OpSchema) -> StrategyType:
    input_strategy = op_schema.args_schema[0]
    dim = op_schema.args_schema[1]
    index_strategy = op_schema.args_schema[2]

    if not isinstance(input_strategy, OpStrategy):
        raise AssertionError(f"Expected OpStrategy, got {type(input_strategy)}")
    if not isinstance(index_strategy, OpStrategy):
        raise AssertionError(f"Expected OpStrategy, got {type(index_strategy)}")
    if not isinstance(dim, int):
        raise AssertionError(f"Expected int, got {type(dim)}")
    dim = normalize_dim(dim, input_strategy.ndim)
    mesh = input_strategy.mesh
    input_shape = input_strategy.shape
    index_shape = index_strategy.shape

    single_mesh_dim_strategies = []

    # placement list stores placements of [output, input, index, src]
    # first we always have replicate all for inputs and output
    all_replicate: PlacementList = [Replicate()] * 4
    single_mesh_dim_strategies.append(all_replicate)

    if len(input_shape) == len(index_shape):
        for d in range(len(input_shape)):
            if d != dim and input_shape[d] == index_shape[d]:
                sharding: PlacementList = [Shard(d), Shard(d), Shard(d), Shard(d)]
                single_mesh_dim_strategies.append(sharding)

    return expand_to_full_mesh_op_strategy(
        mesh, op_schema, single_mesh_dim_strategies, input_index=1
    )