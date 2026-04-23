def get_source_inputs(tensor):
    """Returns the list of input tensors necessary to compute `tensor`.

    Output will always be a list of tensors
    (potentially with 1 element).

    Args:
        tensor: The tensor to start from.

    Returns:
        List of input tensors.
    """
    if not hasattr(tensor, "_keras_history"):
        return tensor

    operation, node_index, _ = tensor._keras_history
    if not operation or not operation._inbound_nodes:
        return [tensor]
    else:
        node = operation._inbound_nodes[node_index]
        if node.is_input:
            # Reached input node, stop recursion.
            return tree.flatten(node.output_tensors)
        else:
            source_tensors = []
            for tensor in node.input_tensors:
                previous_sources = get_source_inputs(tensor)
                # Avoid input redundancy.
                for x in previous_sources:
                    if all(x is not t for t in source_tensors):
                        source_tensors.append(x)
            return source_tensors