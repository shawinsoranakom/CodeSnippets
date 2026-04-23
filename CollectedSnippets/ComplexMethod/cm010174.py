def run_and_get_constant_graph(gm: torch.fx.GraphModule) -> torch.fx.GraphModule:
    """
    Construct a GraphModule which corresponds to the part which could be
    constant folded in provided gm.
    """

    constant_graph_tag(gm)
    # We rewrite the tags, if it's a constant being directly consumed, without
    # any folding opportunity, we keep it in main gm.
    for node in gm.graph.find_nodes(op="get_attr"):
        used_to_fold = False
        for u in node.users:
            if u.meta[META_TAG] == CONST_MODULE_TAG:
                used_to_fold = True
                break
        if not used_to_fold:
            node.meta[META_TAG] = MODULE_TAG

    new_graph = torch.fx.Graph()

    node_remapping: dict[torch.fx.Node, torch.fx.Node] = {}
    output_nodes = []
    for node in gm.graph.nodes:
        if node.meta[META_TAG] == MODULE_TAG:
            continue

        new_node = new_graph.node_copy(node, lambda x: node_remapping[x])
        node_remapping[node] = new_node

        for user in node.users:
            if user.meta[META_TAG] == MODULE_TAG:
                output_nodes.append(new_node)
                break

    new_graph.output(tuple(output_nodes))
    new_graph.lint()
    new_gm = torch.fx.GraphModule(gm, new_graph)

    return new_gm