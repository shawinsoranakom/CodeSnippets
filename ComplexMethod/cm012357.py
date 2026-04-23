def can_reach_amplified_node(
    graph: Graph, amplifier_node: Node, is_fwd: bool
) -> dict[Node, bool]:
    """
    A amplified node means a node with the same numel as `amplifier_node`
    """
    filter_obj: dict[Node, bool] = {}
    nodelist = reversed(graph.nodes) if is_fwd else graph.nodes
    target_numel = get_fake_tensor_from_node_arg(amplifier_node).numel()  # type: ignore[union-attr]

    for node in nodelist:
        reach = False
        if node.op == "output":
            # output node does not have a meta['val']
            reach = False

        elif get_fake_tensor_from_node_arg(node) is None:
            reach = False

        # for the back propagation, we should continue propagate if we can
        # reach a tangent node
        elif get_fake_tensor_from_node_arg(node).numel() == target_numel or (  # type: ignore[union-attr]
            not is_fwd and is_tangent_node(node)
        ):
            reach = True
        else:
            neighbors = node.users if is_fwd else get_args_of_node_type(node)
            reach = any(filter_obj[neighbor] for neighbor in neighbors)
        filter_obj[node] = reach
    return filter_obj