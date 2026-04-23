def expand_fusion_regions(
    gm: fx.GraphModule,
    region_of: dict[fx.Node, FusionRegion],
) -> dict[fx.Node, fx.Node | None]:
    """
    Expand call_module nodes back to their original nodes using _inline_module.

    Returns a mapping from erased module nodes to their replacement (last inlined node).
    This is used with transfer_erased_node_deps to update dependencies.
    """
    from torch.fx.experimental.const_fold import _inline_module

    result: dict[fx.Node, fx.Node | None] = {}

    if not region_of:
        return result

    for module_node, region in list(region_of.items()):
        if module_node.op != "call_module":
            continue

        subgraph_name = module_node.target
        assert isinstance(subgraph_name, str)
        assert hasattr(gm, subgraph_name), (
            f"Expected submodule {subgraph_name} to exist"
        )

        # Users of module_node are get_items that will be removed from the graph
        for user in module_node.users:
            if user.op == "call_function" and user.target == operator.getitem:
                result[user] = None

        # Get the output arg from the subgraph to determine what will replace module_node
        output_arg = torch._inductor.utils.output_node(region.subgraph_module).args[0]

        # Inline the module and get the mapping from subgraph nodes to new nodes.
        # Skip DCE since the graph may not be in a topo ordered state
        subgraph_to_new = _inline_module(gm, subgraph_name, run_dce=False)

        # Map module_node to the replacement for the output arg
        # For multi-output (tuple), use the last element (latest in topo order)
        # so dependencies are only satisfied after all outputs are computed
        if isinstance(output_arg, (list, tuple)):
            if output_arg:
                last_arg = output_arg[-1]
                assert isinstance(last_arg, fx.Node)
                result[module_node] = subgraph_to_new[last_arg]
        elif isinstance(output_arg, fx.Node) and output_arg in subgraph_to_new:
            result[module_node] = subgraph_to_new[output_arg]

        delattr(gm, subgraph_name)

    return result