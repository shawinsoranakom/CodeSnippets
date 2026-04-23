def map_graph(inputs, outputs):
    """Validates a graph's topology and gather its operations and nodes.

    Args:
        inputs: List of input tensors.
        outputs: List of outputs tensors.

    Returns:
        A tuple `(nodes, nodes_by_depth, operations, operations_by_depth)`.
        - nodes: set of Node instances
        - nodes_by_depth: dict mapping ints (depth) to lists of node instances.
        - operations: list of Operation instances.
        - operations_by_depth: dict mapping ints (depth) to lists of Operation
            instances.
    """
    # "depth" is number of operations between output Node and the Node.
    # Nodes are ordered from inputs -> outputs.
    nodes_in_decreasing_depth, operation_indices = _build_map(inputs, outputs)
    nodes_in_graph = set(nodes_in_decreasing_depth)
    network_nodes = {
        make_node_key(node.operation, node.operation._inbound_nodes.index(node))
        for node in nodes_in_decreasing_depth
    }

    nodes_depths = {}  # dict {node: depth value}
    operations_depths = {}  # dict {operation: depth value}

    for node in reversed(nodes_in_decreasing_depth):
        # If the depth is not set, the node has no outbound nodes (depth 0).
        depth = nodes_depths.setdefault(node, 0)

        # Update the depth of the corresponding operation
        previous_depth = operations_depths.get(node.operation, 0)
        # If we've seen this operation before at a higher depth,
        # we should use that depth instead of the node depth.
        # This is necessary for shared operations that have inputs at different
        # depth levels in the graph.
        depth = max(depth, previous_depth)
        operations_depths[node.operation] = depth
        nodes_depths[node] = depth

        # Update the depth of inbound nodes.
        # The "depth" of a node is the max of the depths
        # of all nodes it is connected to + 1.
        # Only update nodes that are actually part of the graph.
        for node_dep in node.parent_nodes:
            if node_dep not in nodes_in_graph:
                continue
            previous_depth = nodes_depths.get(node_dep, 0)
            nodes_depths[node_dep] = max(depth + 1, previous_depth)

    # Handle inputs that are not connected to outputs.
    # We do not error out here because the inputs may be used to compute losses
    # and metrics.
    for input_t in inputs:
        input_operation = input_t._keras_history[0]
        if input_operation and input_operation not in operations_depths:
            node_index = input_t._keras_history.node_index
            node = input_operation._inbound_nodes[node_index]
            # Add InputLayer operations (unused inputs) unconditionally.
            # Skip non-InputLayer operations, as they produce intermediate
            # tensors used as Function inputs and are outside the graph.
            if node.is_input:
                operations_depths[input_operation] = 0
                operation_indices[input_operation] = -1
                nodes_depths[node] = 0
                network_nodes.add(make_node_key(input_operation, node_index))

    # Build a dict {depth: list of nodes with this depth}
    nodes_by_depth = collections.defaultdict(list)
    for node, depth in nodes_depths.items():
        nodes_by_depth[depth].append(node)

    # Build a dict {depth: list of operations with this depth}
    operations_by_depth = collections.defaultdict(list)
    for operation, depth in operations_depths.items():
        operations_by_depth[depth].append(operation)

    # Get sorted list of operation depths.
    depth_keys = list(operations_by_depth.keys())
    depth_keys.sort(reverse=True)

    # Set self.operations ordered by depth.
    operations = []
    for depth in depth_keys:
        operations_for_depth = operations_by_depth[depth]
        # Network.operations needs to have a deterministic order:
        # here we order them by traversal order.
        operations_for_depth.sort(key=lambda x: operation_indices[x])
        operations.extend(operations_for_depth)

    # Get sorted list of node depths.
    depth_keys = list(nodes_by_depth.keys())
    depth_keys.sort(reverse=True)

    # Check that all tensors required are computable.
    # computable_tensors: all tensors in the graph
    # that can be computed from the inputs provided.
    computable_tensors = set()
    for x in inputs:
        computable_tensors.add(x)

    operations_with_complete_input = []  # To provide a better error msg.
    for depth in depth_keys:
        for node in nodes_by_depth[depth]:
            for x in tree.flatten(node.input_tensors):
                if x not in computable_tensors:
                    operation = node.operation
                    raise ValueError(
                        "Graph disconnected: cannot find parent for "
                        f"tensor {x} at operation '{operation}'. "
                        "The following previous operations were accessed "
                        f"without issue: {operations_with_complete_input}"
                    )
                operations_with_complete_input.append(node.operation.name)

            for x in tree.flatten(node.outputs):
                computable_tensors.add(x)

    # Ensure name unicity, which will be crucial for serialization
    # (since serialized nodes refer to operations by their name).
    all_names = [operation.name for operation in operations]
    for name in all_names:
        if all_names.count(name) != 1:
            raise ValueError(
                f'The name "{name}" is used {all_names.count(name)} '
                "times in the model. All operation names should be unique."
            )
    return network_nodes, nodes_by_depth, operations, operations_by_depth