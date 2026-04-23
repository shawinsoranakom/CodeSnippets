def _name_hoo_subgraph_placeholders(gm: torch.fx.GraphModule) -> None:
    """
    Propagate placeholder names from the top-level graph into HigherOrderOp subgraphs,
    and handle collisions with non-placeholders by count suffixing.
    Different HOO subgraph types have different input schemas, so we first enumerate them
    and gather the top-level named placeholder nodes.
    """

    # gather all HOO subgraphs and their top-level named placeholder nodes
    subgraph_ph_tuples: list[tuple[torch.fx.GraphModule, list[torch.fx.Node]]] = []
    for node in gm.graph.nodes:
        if node.op == "call_function" and isinstance(
            node.target, torch._ops.HigherOrderOperator
        ):
            # HOO subgraphs have varying input schemas, so we enumerate them there
            if node.target._name == "cond":
                _, true_graph, false_graph, cond_args = node._args
                subgraph_ph_tuples.append((getattr(gm, true_graph.target), cond_args))
                subgraph_ph_tuples.append((getattr(gm, false_graph.target), cond_args))
            elif node.target._name == "wrap_with_set_grad_enabled":
                subgraph, phs = node._args[1], node._args[2:]
                subgraph_ph_tuples.append((getattr(gm, subgraph.target), phs))
            elif node.target._name == "map_impl":
                body_graph, array, args = node._args
                subgraph_ph_tuples.append(
                    (getattr(gm, body_graph.target), array + args)
                )

    # propagate names
    for subgraph, hoo_phs in subgraph_ph_tuples:
        name_map: dict[str, str] = {}
        find_available: dict[str, int] = defaultdict(int)
        used_names: set[str] = set()
        for i, node in enumerate(subgraph.graph.nodes):
            if i < len(hoo_phs):  # placeholder, retain name
                name_map[node.name] = hoo_phs[i].name
                node.name = node.target = hoo_phs[i].name
                _build_cache(node.name, find_available, used_names)
            else:  # non-placeholder, check for collisions
                node.name = _rename_without_collisions(
                    name_map, find_available, used_names, node.name, node.name
                )

        # recurse and recompile
        _name_hoo_subgraph_placeholders(subgraph)
        subgraph.recompile()