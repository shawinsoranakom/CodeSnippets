def foreach_group_loop(groups, num_outputs, apply_fn, realize_outputs):
    """
    Common loop over grouped foreach arguments.

    Args:
        groups: Result of group_foreach_args - dict mapping (device, use_foreach) to groups
        num_outputs: Number of outputs to produce
        apply_fn: Function to apply to each set of args, returns the output
        realize_outputs: Whether to realize outputs for foreach fusion
    """
    outputs = [None] * num_outputs
    for (device, use_foreach), group in groups.items():
        operation_list: list[str] = []
        for output_ind, args in group:
            output = apply_fn(args)
            outputs[output_ind] = output

            if (
                V.graph.has_feature(device, BackendFeature.FOREACH)
                and use_foreach
                and realize_outputs
            ):
                output.realize()
                operation_list.append(output.get_operation_name())

        if operation_list:
            V.graph.register_operation_list(operation_list)

    assert all(x is not None for x in outputs)
    return outputs