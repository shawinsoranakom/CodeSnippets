def sort_chat_inputs_first(
    vertices_layers: list[list[str]],
    get_vertex_predecessors: Callable[[str], list[str]],
) -> list[list[str]]:
    """Sorts the vertices so that chat inputs come first in the layers.

    Only one chat input is allowed in the entire graph.

    Args:
        vertices_layers: List of layers, where each layer is a list of vertex IDs
        get_vertex_predecessors: Function to get the predecessor IDs of a vertex

    Returns:
        Sorted layers with single chat input first

    Raises:
        ValueError: If there are multiple chat inputs in the graph
    """
    chat_input = None
    chat_input_layer_idx = None

    # Find chat input and validate only one exists
    for layer_idx, layer in enumerate(vertices_layers):
        for vertex_id in layer:
            if "ChatInput" in vertex_id and get_vertex_predecessors(vertex_id):
                return vertices_layers
            if "ChatInput" in vertex_id:
                if chat_input is not None:
                    msg = "Only one chat input is allowed in the graph"
                    raise ValueError(msg)
                chat_input = vertex_id
                chat_input_layer_idx = layer_idx

    if not chat_input:
        return vertices_layers
    # If chat input already in first layer, just move it to index 0
    if chat_input_layer_idx == 0:
        # If chat input is alone in first layer, keep as-is
        if len(vertices_layers[0]) == 1:
            return vertices_layers

        # Otherwise move chat input to its own layer at the start
        vertices_layers[0].remove(chat_input)
        return [[chat_input], *vertices_layers]

    # Otherwise create new layers with chat input first
    result_layers = []
    for layer in vertices_layers:
        layer_vertices = [v for v in layer if v != chat_input]
        if layer_vertices:
            result_layers.append(layer_vertices)

    return [[chat_input], *result_layers]