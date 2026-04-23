def refine_layers(
    initial_layers: list[list[str]],
    successor_map: dict[str, list[str]],
) -> list[list[str]]:
    """Refines the layers of vertices to ensure proper dependency ordering.

    Args:
        initial_layers: Initial layers of vertices
        successor_map: Map of vertex IDs to their successors

    Returns:
        Refined layers with proper dependency ordering
    """
    # Map each vertex to its current layer
    vertex_to_layer: dict[str, int] = {}
    for layer_index, layer in enumerate(initial_layers):
        for vertex in layer:
            vertex_to_layer[vertex] = layer_index

    refined_layers: list[list[str]] = [[] for _ in initial_layers]  # Start with empty layers
    new_layer_index_map = defaultdict(int)

    # Map each vertex to its new layer index
    # by finding the lowest layer index of its dependencies
    # and subtracting 1
    # If a vertex has no dependencies, it will be placed in the first layer
    # If a vertex has dependencies, it will be placed in the lowest layer index of its dependencies
    # minus 1
    for vertex_id, deps in successor_map.items():
        indexes = [vertex_to_layer[dep] for dep in deps if dep in vertex_to_layer]
        new_layer_index = max(min(indexes, default=0) - 1, 0)
        new_layer_index_map[vertex_id] = new_layer_index

    for layer_index, layer in enumerate(initial_layers):
        for vertex_id in layer:
            # Place the vertex in the highest possible layer where its dependencies are met
            new_layer_index = new_layer_index_map[vertex_id]
            if new_layer_index > layer_index:
                refined_layers[new_layer_index].append(vertex_id)
                vertex_to_layer[vertex_id] = new_layer_index
            else:
                refined_layers[layer_index].append(vertex_id)

    # Remove empty layers if any
    return [layer for layer in refined_layers if layer]