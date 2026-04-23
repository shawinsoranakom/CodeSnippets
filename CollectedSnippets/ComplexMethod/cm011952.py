def split_const_gm(
    gm: GraphModule,
    skip_constructor: bool = True,
    lifted_constant_names: list[str] | None = None,
    skip_folding_node_fn: Callable[[torch.fx.Node], bool] | None = None,
) -> tuple[GraphModule, dict[str, int]]:
    """
    This function takes an GraphModule input "gm".
    The gm will be split into 2 components,
      1) const_gm, which consists the subgraph of gm that can be constant folded.
      2) gm (being inplace modified,) which returns the graph after constant folding.

    If an additional "lifted_constants" argument is passed in, we will assume the gm has
    been lifted and run the transformation accordingly.

    When a "skip_folding_node_fn" callback is passed, we will skip constant folding on
    the nodes for which the callback returns True.

    const_output_index is a mapping of corresponding node name from gm to the
    output index of const_gm.
    Returns (const_gm, const_output_index)
    """
    from torch._inductor.constant_folding import (
        CONST_MODULE_TAG,
        META_TAG,
        MODULE_TAG,
        replace_node_with_constant,
        run_and_get_constant_graph,
    )

    const_gm = run_and_get_constant_graph(
        gm, skip_constructor, lifted_constant_names, skip_folding_node_fn
    )
    const_result = const_gm() if lifted_constant_names is None else None

    const_outputs = {
        x.name: idx for idx, x in enumerate(tuple(const_gm.graph.nodes)[-1].args[0])
    }

    to_erase_node = []
    to_replace_node = []
    const_output_index = {}
    for node in gm.graph.nodes:
        if node.name in const_outputs:
            to_replace_node.append(node)
        elif node.meta[META_TAG] == CONST_MODULE_TAG and node.op != "placeholder":
            to_erase_node.append(node)

    for node in to_replace_node:
        new_const_name = "_FOLDED_CONST_" + node.name
        replace_node_with_constant(
            gm,
            node,
            (
                const_result[const_outputs[node.name]]  # type:ignore[index]
                if lifted_constant_names is None
                else None
            ),
            new_const_name,
        )
        const_output_index[new_const_name] = const_outputs[node.name]
    for node in to_erase_node[::-1]:
        if node.users:
            for n in node.users:
                assert n.meta[META_TAG] == MODULE_TAG, f"node: {node} user not empty."
        else:
            gm.graph.erase_node(node)
    gm.recompile()

    return const_gm, const_output_index