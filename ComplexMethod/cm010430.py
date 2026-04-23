def inline_single_use_recursive(gm: GraphModule, global_counts: Counter[str]) -> None:
    # Recursively apply to nested subgraph modules first.
    for name, mod in gm.named_modules():
        if name and isinstance(mod, GraphModule):
            inline_single_use_recursive(mod, global_counts)

    invoke_nodes = list(
        gm.graph.find_nodes(
            op="call_function", target=torch.ops.higher_order.invoke_subgraph
        )
    )
    if not invoke_nodes:
        return

    single_use_nodes = [
        node for node in invoke_nodes if global_counts[str(node.args[1])] == 1
    ]
    if not single_use_nodes:
        return

    inline_invoke_subgraph_nodes(gm, single_use_nodes)