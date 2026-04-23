def test_get_sorted_vertices_with_unconnected_graph():
    # Define a graph with the specified structure
    vertices_ids = ["A", "B", "C", "D", "K"]
    cycle_vertices = set()
    graph_dict = {
        "A": {"successors": ["B"], "predecessors": []},
        "C": {"successors": ["B"], "predecessors": []},
        "B": {"successors": ["D"], "predecessors": ["A", "C"]},
        "D": {"successors": [], "predecessors": ["B"]},
        "K": {"successors": [], "predecessors": []},
    }
    in_degree_map = {vertex: len(data["predecessors"]) for vertex, data in graph_dict.items()}
    successor_map = {vertex: data["successors"] for vertex, data in graph_dict.items()}
    predecessor_map = {vertex: data["predecessors"] for vertex, data in graph_dict.items()}

    def is_input_vertex(vertex_id: str) -> bool:
        return vertex_id == "A"

    def get_vertex_predecessors(vertex_id: str) -> list[str]:
        return predecessor_map[vertex_id]

    def get_vertex_successors(vertex_id: str) -> list[str]:
        return successor_map[vertex_id]

    first_layer, remaining_layers = utils.get_sorted_vertices(
        vertices_ids=vertices_ids,
        cycle_vertices=cycle_vertices,
        stop_component_id=None,
        start_component_id="A",
        graph_dict=graph_dict,
        in_degree_map=in_degree_map,
        successor_map=successor_map,
        predecessor_map=predecessor_map,
        is_input_vertex=is_input_vertex,
        get_vertex_predecessors=get_vertex_predecessors,
        get_vertex_successors=get_vertex_successors,
        is_cyclic=False,
    )

    # Verify the first layer contains all input vertices
    assert set(first_layer) == {"A", "C"}

    # Verify the remaining layers contain the rest of the vertices in the correct order
    assert len(remaining_layers) == 2
    assert remaining_layers[0] == ["B"]
    assert remaining_layers[1] == ["D"]