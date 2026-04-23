def detect_exists_identical_opspec(*args, op, mesh, strategy_function) -> bool:
    """
    Given sample input args, detect if identical OpSpecs exists under the same
    OpStrategy.

    """
    tree_args = tree_leaves(args)
    # metadata for each argument
    arg_tensor_metadata = [extract_tensor_meta(i) for i in args]
    # possible combination of placements for each arg
    arg_placement_comb = []
    for i in tree_args:
        if isinstance(i, torch.Tensor):
            # possible placement choice for argument i
            placement_choices = (Replicate(), *[Shard(i) for i in range(i.ndim)])
            # expand placement choice into full Placements for argument i
            arg_placement_comb.append(
                list(itertools.product(placement_choices, repeat=mesh.ndim))
            )
            random.shuffle(arg_placement_comb[-1])

    arg_opspec_list = []
    for idx, arg_placement in enumerate(arg_placement_comb):
        arg_opspec_list.append([])
        for placement in arg_placement:
            arg_opspec_list[idx].append(
                OpSpec(
                    output_specs=DTensorSpec(
                        mesh, placement, tensor_meta=arg_tensor_metadata[idx]
                    )
                )
            )

    op_schema = OpSchema(
        op,
        args_schema=(tuple(OpStrategy(i) for i in arg_opspec_list)),
        kwargs_schema={},
    )
    with op_strategy_context(op, strategy_function):
        output_strategy = strategy_function(op_schema)
        # OpSpec doesn't have hashing, convert to str to compare
        output_strategy_str_list = [
            str(j) for i in tree_leaves(output_strategy) for j in i.strategies
        ]
        return len(output_strategy_str_list) == len(set(output_strategy_str_list))