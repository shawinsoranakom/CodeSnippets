def find_amplifier_node(graph: Graph) -> Node | None:
    r"""
    Find the 'amplifier' node which is a node that generates large
    output with small/medium input.

    If there are multiple amplifier nodes, return the one with the largest
    amplification ratio.
    """

    amplifier_nodes_ratio = []

    for node in graph.nodes:
        if use_tangent(node):
            # enter backward part of the graph
            break

        # Only trigger chunking for a small set of nodes like matmul for now
        if node.op != "call_function" or node.target not in eligible_amplifier_node:
            continue

        input_size = compute_tensor_size(node.args, node.kwargs)
        output_size = compute_tensor_size(node)

        if input_size == 0:
            continue

        ratio = output_size / input_size
        if (
            output_size > config.auto_chunker.output_size_threshold
            and ratio > config.auto_chunker.amplify_ratio_threshold
        ):
            amplifier_nodes_ratio.append((node, ratio))

    amplifier_nodes_ratio = sorted(
        amplifier_nodes_ratio, key=lambda x: x[1], reverse=True
    )
    return amplifier_nodes_ratio[0][0] if len(amplifier_nodes_ratio) > 0 else None