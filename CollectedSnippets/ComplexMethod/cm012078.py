def replace_params_with_constants(
    gm: torch.fx.GraphModule,
    flat_params: list[Any],
    fw_metadata: torch._functorch.aot_autograd.ViewAndMutationMeta,
) -> list[int]:
    """
    Replaces the parameters of a PyTorch GraphModule with constants wherever possible.
    Returns a list of indices representing the input parameters that were not converted to constants.
    """
    params = gm.graph.find_nodes(op="placeholder")
    fake_inp_nodes = params[: len(params)]
    preserved_arg_indices = []
    aliased_input_args = [
        out_info.base_idx
        for out_info in fw_metadata.output_info
        if out_info.base_idx is not None
    ]

    # TODO (tmanlaibaatar) figure out why this is different
    # from mutated_inp_runtime_indices
    mutated_inps = [
        i
        for i, m in enumerate(fw_metadata.input_info)
        if m.mutation_type
        in (MutationType.MUTATED_IN_GRAPH, MutationType.MUTATED_OUT_GRAPH)
    ]

    static_indices_new = []
    static_indices_offset = 0
    for i, (real_input, node) in enumerate(zip(flat_params, fake_inp_nodes)):
        if i in mutated_inps or i in aliased_input_args:
            preserved_arg_indices.append(i)
            if i in fw_metadata.static_input_indices:
                new_static_index = i - static_indices_offset
                static_indices_new.append(new_static_index)
        else:
            replace_node_with_constant(gm, node, real_input)
            static_indices_offset += 1
    # add on non param inputs
    preserved_arg_indices.extend(range(len(flat_params), len(params)))
    # is this necessary ?
    fw_metadata.static_input_indices = static_indices_new
    gm.recompile()
    return preserved_arg_indices