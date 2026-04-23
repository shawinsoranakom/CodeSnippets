def _collect_all_subgraph_usages(
    gm: torch.fx.GraphModule,
    subgraph_id_to_callers: dict[
        int, list[tuple[torch.fx.GraphModule, str, torch.fx.Node]]
    ],
) -> None:
    """Recursively collect all HOP usages across the graph tree."""
    for node in gm.graph.nodes:
        if node.op == "call_function" and node.target in _HOPS_WITH_EXTRA_OUTPUTS:
            subgraph_attr = node.args[0]
            if (
                isinstance(subgraph_attr, torch.fx.Node)
                and subgraph_attr.op == "get_attr"
            ):
                subgraph_name = subgraph_attr.target
                assert isinstance(subgraph_name, str)
                subgraph = getattr(gm, subgraph_name, None)
                if isinstance(subgraph, torch.fx.GraphModule):
                    subgraph_id = id(subgraph)
                    subgraph_id_to_callers[subgraph_id].append(
                        (gm, subgraph_name, node)
                    )
                    _collect_all_subgraph_usages(subgraph, subgraph_id_to_callers)