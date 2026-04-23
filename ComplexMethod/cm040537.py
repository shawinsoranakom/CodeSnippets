def _build_map_helper(
    inputs,
    tensor,
    finished_nodes,
    nodes_in_progress,
    nodes_in_decreasing_depth,
    operation_indices,
):
    """Recursive helper for `_build_map`."""
    (
        operation,
        node_index,
        _,
    ) = tensor._keras_history
    if not operation:
        return

    node = operation._inbound_nodes[node_index]

    # Don't repeat work for shared subgraphs
    if node in finished_nodes:
        return

    # If this tensor is one of the declared inputs and its producing
    # operation is not an InputLayer, stop traversal here. The operation
    # that produced this tensor is outside the Function's graph.
    flat_inputs = tree.flatten(inputs)
    if not node.is_input and tensor in flat_inputs:
        finished_nodes.add(node)
        return

    # Prevent cycles.
    if node in nodes_in_progress:
        raise ValueError(
            f"Tensor {tensor} from operation '{operation.name}' is part of a "
            "cycle."
        )

    # Store the traversal order for operation sorting.
    if operation not in operation_indices:
        operation_indices[operation] = len(operation_indices)

    # Propagate to all previous tensors connected to this node.
    nodes_in_progress.add(node)
    if not node.is_input:
        for input_tensor in node.input_tensors:
            _build_map_helper(
                inputs,
                input_tensor,
                finished_nodes,
                nodes_in_progress,
                nodes_in_decreasing_depth,
                operation_indices,
            )

    finished_nodes.add(node)
    nodes_in_progress.remove(node)
    nodes_in_decreasing_depth.append(node)