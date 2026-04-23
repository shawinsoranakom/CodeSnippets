def reordering_to_mimic_autograd_engine(gm: fx.GraphModule) -> fx.GraphModule:
    """
    This pass finds the first bwd node in the graph (by looking at users of
    tangents) and then reorders the graph by walking from this node to all the
    way to the end of the graph. At each op in this traversal, we insert this op
    in a new graph and try to bring only the relevant subgraph from the other
    non-bwd edges relevant for this op. This closely mimics the behavior of
    autograd engine.

    Why is this pass required in the first place?

    This is an artifact of how partitioners work today. The starting point of
    partitioner is a joint graph, which is fwd and then bwd graph. In the case
    of checkpointing, we keep portions of fwd graph in their original place in
    the joint graph, while obtaining a bwd graph. As a result, the resulting bwd
    graph has copies of recomputed fwd subgraphs followed by the original bwd
    graph. If we run this naively, this leads to bad memory footprint, because
    the fwd subgraphs are live for way longer duration than necessary. This pass
    reorders the operations such that we prioritize the ops for the original bwd
    graph while only realizing those ops from the fwd graph that are necessary
    at any given point in the graph.
    """

    new_graph = fx.Graph()
    env: dict[fx.Node, fx.Node] = {}

    # Add new placeholder nodes in the order specified by the inputs
    for node in gm.graph.find_nodes(op="placeholder"):
        env[node] = new_graph.node_copy(node, lambda x: env[x])

    order = {node: idx for idx, node in enumerate(gm.graph.nodes)}

    def insert_node_in_graph(node: fx.Node) -> None:
        cur_nodes = [node]
        insertable_nodes: OrderedSet[fx.Node] = OrderedSet()
        while len(cur_nodes) > 0:
            node = cur_nodes.pop()
            if node in insertable_nodes or node in env:
                continue
            insertable_nodes.add(node)

            # Bias traversal towards the nodes that have higher depth - prioritizes
            # critical path first.
            cur_nodes += node.all_input_nodes

        # pyrefly: ignore [bad-assignment]
        insertable_nodes = sorted(insertable_nodes, key=lambda n: order[n])
        for node in insertable_nodes:
            env[node] = new_graph.node_copy(node, lambda x: env[x])

    # Find first bwd node in the graph
    tangent_inputs = list(filter(_is_tangent, gm.graph.nodes))
    first_node_in_bwd = None
    minimum_order = math.inf
    for tangent in tangent_inputs:
        for user in tangent.users:
            if order[user] < minimum_order:
                minimum_order = order[user]
                first_node_in_bwd = user

    # If gradInp does not depend upon gradOut, we may not find any nodes in the "backwards pass"
    if first_node_in_bwd is None:
        return gm

    # Build the graph op-by-op by starting from the node all the way to the end
    # copy_ can be not using tangents at all, we must copy it.
    for node in list(gm.graph.nodes)[: order[first_node_in_bwd]]:
        if node.op == "call_function" and node.target is torch.ops.aten.copy_.default:
            insert_node_in_graph(node)

    for node in list(gm.graph.nodes)[order[first_node_in_bwd] :]:
        insert_node_in_graph(node)

    # The output node is already built by the traversal.
    new_gm = torch.fx.GraphModule(gm, new_graph)
    return new_gm