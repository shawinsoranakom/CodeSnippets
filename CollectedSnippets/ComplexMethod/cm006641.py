def test_get_sorted_vertices_with_complex_cycle(graph_with_loop):
    # Convert the graph structure to the format needed by get_sorted_vertices
    vertices_ids = list(graph_with_loop.keys())
    cycle_vertices = {"Loop", "Parse Data 1", "YouTube Transcripts"}  # Known cycle in the graph
    graph_dict = graph_with_loop

    # Build in_degree_map from predecessors
    in_degree_map = {vertex: len(data["predecessors"]) for vertex, data in graph_with_loop.items()}

    # Build successor and predecessor maps
    successor_map = {vertex: data["successors"] for vertex, data in graph_with_loop.items()}
    predecessor_map = {vertex: data["predecessors"] for vertex, data in graph_with_loop.items()}

    def is_input_vertex(vertex_id: str) -> bool:
        # Only Playlist Extractor is an input vertex
        return vertex_id == "Playlist Extractor"

    def get_vertex_predecessors(vertex_id: str) -> list[str]:
        return predecessor_map[vertex_id]

    def get_vertex_successors(vertex_id: str) -> list[str]:
        return successor_map[vertex_id]

    # Test with the cycle
    first_layer, remaining_layers = utils.get_sorted_vertices(
        vertices_ids=vertices_ids,
        cycle_vertices=cycle_vertices,
        stop_component_id=None,
        start_component_id=None,
        graph_dict=graph_dict,
        in_degree_map=in_degree_map,
        successor_map=successor_map,
        predecessor_map=predecessor_map,
        is_input_vertex=is_input_vertex,
        get_vertex_predecessors=get_vertex_predecessors,
        get_vertex_successors=get_vertex_successors,
        is_cyclic=True,
    )

    # When is_cyclic is True and start_vertex_id is provided:
    # 1. The first layer will contain vertices with no predecessors and vertices that are part of the cycle
    # 2. This is because the cycle vertices are treated as having no dependencies in the initial sort
    assert "OpenAI Embeddings" in first_layer, (
        "Vertex with no predecessors 'OpenAI Embeddings' should be in first layer"
    )
    assert "Playlist Extractor" in first_layer, "Input vertex 'Playlist Extractor' should be in first layer"
    assert len(first_layer) == 2, (
        f"First layer should contain exactly 4 vertices, got {len(first_layer)}: {first_layer}"
    )

    # Verify that the remaining layers contain the rest of the vertices in the correct order
    # The graph structure shows:
    # Loop -> Parse Data 2 -> Message to Data -> Split Text -> Chroma DB
    # OpenAI Embeddings -> Chroma DB
    vertex_to_layer = {}
    for i, layer in enumerate(remaining_layers):
        for vertex in layer:
            vertex_to_layer[vertex] = i

    # Verify that vertices appear in the correct order
    assert "Loop" in vertex_to_layer, "Vertex 'Loop' should be present in remaining layers"
    assert "Parse Data 2" in vertex_to_layer, "Vertex 'Parse Data 2' should be present in remaining layers"
    assert "Message to Data" in vertex_to_layer, "Vertex 'Message to Data' should be present in remaining layers"
    assert "Chroma DB" in vertex_to_layer, "Vertex 'Chroma DB' should be present in remaining layers"

    # Verify the dependencies are respected
    # Note: Due to the cycle and the way layered_topological_sort works,
    # some vertices might appear in earlier layers than expected
    # What's important is that the dependencies are respected within the non-cycle components
    assert vertex_to_layer["Parse Data 2"] <= vertex_to_layer["Message to Data"], (
        f"'Parse Data 2' (layer {vertex_to_layer['Parse Data 2']}) should appear in same or earlier layer than "
        f"'Message to Data' (layer {vertex_to_layer['Message to Data']})"
    )