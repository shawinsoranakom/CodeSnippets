def split_strategy(op_schema: OpSchema) -> OpStrategy:
    input_strategy = op_schema.args_schema[0]
    split_size_or_sections = op_schema.args_schema[1]
    if not isinstance(input_strategy, OpStrategy):
        raise AssertionError(f"Expected OpStrategy, got {type(input_strategy)}")
    input_ndim = input_strategy.ndim
    split_dim = (
        cast(int, op_schema.args_schema[2]) if len(op_schema.args_schema) > 2 else 0
    )
    dim = normalize_dim(split_dim, input_ndim)

    def size_split(N, i) -> list:
        # Last chunk will be smaller if the tensor size N
        # along the given dimension dim is not divisible by i.
        if not i > 0:
            raise AssertionError(f"Split size must be positive, got {i}")
        return [i] * (N // i) + ([N % i] if N % i != 0 else [])

    output_size_list = (
        size_split(input_strategy.shape[dim], split_size_or_sections)
        if isinstance(split_size_or_sections, IntLike)
        else split_size_or_sections
    )
    if not isinstance(output_size_list, Sized):
        raise AssertionError(f"Expected Sized, got {type(output_size_list)}")

    all_strategies = []
    for strategy in input_strategy.strategies:
        spec = strategy.output_spec
        placements = spec.placements
        if is_tensor_dim_sharded(spec, dim=dim):
            # if the input is sharded on the split dim, we need to unshard it
            placements = unshard_tensor_dim(spec.placements, dim=dim)

        input_spec = DTensorSpec(spec.device_mesh, placements, spec.tensor_meta)
        output_specs = tuple(
            DTensorSpec(spec.device_mesh, placements)
            for _ in range(len(output_size_list))
        )
        all_strategies.append(
            OpSpec(
                output_specs=output_specs,
                input_specs=(input_spec,),
                redistribute_cost=[
                    generate_redistribute_costs(input_strategy, input_spec)
                ],
            )
        )

    return OpStrategy(all_strategies)