def cat_strategy(op_schema: OpSchema) -> StrategyType:
    args_schema = op_schema.args_schema
    input_tuple_strategy = args_schema[0]
    if not isinstance(input_tuple_strategy, TupleStrategy):
        raise AssertionError(f"Expected TupleStrategy, got {input_tuple_strategy}")
    num_input_tensor = len(input_tuple_strategy.children)
    first_input_strategy = input_tuple_strategy.children[0]
    if not isinstance(first_input_strategy, OpStrategy):
        raise AssertionError(f"Expected OpStrategy, got {first_input_strategy}")
    common_input_ndim = first_input_strategy.ndim
    dim = cast(int, args_schema[1]) if len(args_schema) > 1 else 0
    # normalize the dim to be within the common input ndim
    dim = normalize_dim(dim, common_input_ndim)

    mesh = first_input_strategy.mesh

    op_strategy = OpStrategy([])
    # use a set to deduplicate strategies with the same placement
    strategies_placement_pool = set()
    for this_strategy in input_tuple_strategy.children:
        # check strategy of each tensor to be concatenated
        if not isinstance(this_strategy, OpStrategy):
            raise AssertionError(f"Expected OpStrategy, got {type(this_strategy)}")
        if this_strategy.mesh != mesh:
            raise AssertionError("cat op doesn't support cross mesh concatenation")
        for op_spec in this_strategy.strategies:
            # Check each OpSpec of the tensor, the placement in this OpSpec
            # is used as the exemplar strategy that other tensors and output
            # tensor should follow. We also need to deduplicate the output
            # strategy with the same placement.
            if not isinstance(op_spec, OpSpec):
                raise AssertionError(f"Expected OpSpec, got {type(op_spec)}")
            # exemplar OpSpec to follow
            exemplar_spec = op_spec.output_spec
            # check if the tensor is sharded on the concat dim
            if is_tensor_dim_sharded(exemplar_spec, dim):
                # if the tensor is sharded on the concat dim, we need to unshard it
                # first
                exemplar_placement = unshard_tensor_dim(exemplar_spec.placements, dim)
            else:
                exemplar_placement = exemplar_spec.placements
            if exemplar_placement not in strategies_placement_pool:
                strategies_placement_pool.add(exemplar_placement)
                # assert isinstance(exemplar_placement, Tuple)
                redistribute_costs = []
                input_specs = []
                for idx in range(num_input_tensor):
                    # extract the strategy for the idx tensors to build the tensor_metadata and redistribute_cost
                    that_tensor_strategy = input_tuple_strategy.children[idx]
                    if not isinstance(that_tensor_strategy, OpStrategy):
                        raise AssertionError(
                            f"Expected OpStrategy, got {type(that_tensor_strategy)}"
                        )
                    input_spec = DTensorSpec(
                        mesh,
                        exemplar_placement,
                        tensor_meta=that_tensor_strategy.strategies[
                            0
                        ].output_spec.tensor_meta,
                    )
                    input_specs.append(input_spec)
                    redistribute_costs.append(
                        generate_redistribute_costs(that_tensor_strategy, input_spec)
                    )
                op_strategy.strategies.append(
                    OpSpec(
                        output_specs=DTensorSpec(mesh, exemplar_placement),
                        input_specs=tuple(input_specs),
                        redistribute_cost=redistribute_costs,
                    )
                )
    return op_strategy