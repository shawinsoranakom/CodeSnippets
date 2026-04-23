def classify_nodes(
    joint_module: fx.GraphModule,
    static_lifetime_input_indices: list[int],
    num_fwd_outputs: int,
) -> NodeInfo:
    name_to_node = get_name_to_node(joint_module.graph)
    required_bw_nodes: OrderedSet[fx.Node] = OrderedSet()
    for node in joint_module.graph.nodes:
        if node.op == "placeholder" and "tangents" in node.target:
            required_bw_nodes.add(node)
        elif _must_be_in_backward(node):
            required_bw_nodes.add(node)

        if node in required_bw_nodes:
            required_bw_nodes.update(node.users)

    primal_inputs = list(filter(_is_primal, joint_module.graph.nodes))
    fwd_seed_offset_inputs = list(filter(_is_fwd_seed_offset, joint_module.graph.nodes))
    inputs = primal_inputs + fwd_seed_offset_inputs
    fwd_outputs, bwd_outputs, fwd_outputs_descs, bwd_outputs_descs = (
        _extract_fwd_bwd_outputs(joint_module, num_fwd_outputs=num_fwd_outputs)
    )
    # Note: [tangents_closure vs required_bw_nodes]
    #
    # required_bw_nodes is used to determine which nodes need edges to
    # the sink. It is important to also track tangents closure because
    # that determines whether you can save that tensor, i.e., whether you
    # want to connect x_in or x_out to the sink.
    tangents_closure = required_bw_nodes.copy()
    required_bw_nodes.update(
        o for o in bwd_outputs if o is not None and o.op != "output"
    )
    forward_only_graph = _extract_graph_with_inputs_outputs(
        joint_module.graph, inputs, fwd_outputs, fwd_outputs_descs, "forward"
    )
    required_fw_nodes: OrderedSet[fx.Node] = OrderedSet(
        name_to_node[node.name]
        for node in forward_only_graph.nodes
        if node.op != "output"
    )
    unclaimed_nodes: OrderedSet[fx.Node] = OrderedSet(
        node
        for node in joint_module.graph.nodes
        if node not in required_fw_nodes and node not in required_bw_nodes
    )
    static_lifetime_input_nodes = OrderedSet(
        p for i, p in enumerate(primal_inputs) if i in static_lifetime_input_indices
    )
    fw_cnt = 0
    fw_order = {}
    for node in joint_module.graph.nodes:
        if node in required_fw_nodes:
            fw_order[node] = fw_cnt
            fw_cnt += 1
    return NodeInfo(
        inputs,
        required_fw_nodes,
        required_bw_nodes,
        tangents_closure,
        unclaimed_nodes,
        fw_order,
        static_lifetime_input_nodes,
    )