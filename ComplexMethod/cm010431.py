def inline_invoke_subgraph_nodes(gm: GraphModule, invoke_nodes: list["Node"]) -> None:
    """Shared helper that inlines a list of invoke_subgraph nodes."""
    for node in invoke_nodes:
        get_attr_node: torch.fx.Node = node.args[0]  # pyrefly: ignore[bad-assignment]
        operands = node.args[2:]

        subgraph: GraphModule = getattr(gm, str(get_attr_node.target))

        env: dict[Node, Any] = dict(
            zip(subgraph.graph.find_nodes(op="placeholder"), operands)
        )

        with gm.graph.inserting_before(node):
            for sub_node in subgraph.graph.nodes:
                if sub_node.op in ("placeholder", "output"):
                    continue
                env[sub_node] = gm.graph.node_copy(sub_node, lambda n: env[n])

        output_values = subgraph.graph.output_node().args[0]

        for user in list(node.users):
            if user.op == "call_function" and user.target is operator.getitem:
                idx = user.args[1]
                user.replace_all_uses_with(env[output_values[idx]])  # pyrefly: ignore
                gm.graph.erase_node(user)

        gm.graph.erase_node(node)

        if not get_attr_node.users:
            gm.graph.erase_node(get_attr_node)