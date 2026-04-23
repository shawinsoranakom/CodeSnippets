def test_filter_vertices_from_vertex():
    # Test case 1: Simple linear graph
    vertices_ids = ["A", "B", "C", "D"]
    graph_dict = {
        "A": {"successors": ["B"], "predecessors": []},
        "B": {"successors": ["C"], "predecessors": ["A"]},
        "C": {"successors": ["D"], "predecessors": ["B"]},
        "D": {"successors": [], "predecessors": ["C"]},
    }

    # Starting from A should return all vertices
    result = utils.filter_vertices_from_vertex(vertices_ids, "A", graph_dict=graph_dict)
    assert result == {"A", "B", "C", "D"}

    # Starting from B should return B, C, D
    result = utils.filter_vertices_from_vertex(vertices_ids, "B", graph_dict=graph_dict)
    assert result == {"B", "C", "D"}

    # Starting from D should return only D
    result = utils.filter_vertices_from_vertex(vertices_ids, "D", graph_dict=graph_dict)
    assert result == {"D"}

    # Test case 2: Graph with branches
    vertices_ids = ["A", "B", "C", "D", "E"]
    graph_dict = {
        "A": {"successors": ["B", "C"], "predecessors": []},
        "B": {"successors": ["D"], "predecessors": ["A"]},
        "C": {"successors": ["E"], "predecessors": ["A"]},
        "D": {"successors": [], "predecessors": ["B"]},
        "E": {"successors": [], "predecessors": ["C"]},
    }

    # Starting from A should return all vertices
    result = utils.filter_vertices_from_vertex(vertices_ids, "A", graph_dict=graph_dict)
    assert result == {"A", "B", "C", "D", "E"}

    # Starting from B should return B and D
    result = utils.filter_vertices_from_vertex(vertices_ids, "B", graph_dict=graph_dict)
    assert result == {"B", "D"}

    # Test case 3: Graph with unconnected vertices
    vertices_ids = ["A", "B", "C", "X", "Y"]
    graph_dict = {
        "A": {"successors": ["B"], "predecessors": []},
        "B": {"successors": ["C"], "predecessors": ["A"]},
        "C": {"successors": [], "predecessors": ["B"]},
        "X": {"successors": ["Y"], "predecessors": []},
        "Y": {"successors": [], "predecessors": ["X"]},
    }

    # Starting from A should return only A, B, C
    result = utils.filter_vertices_from_vertex(vertices_ids, "A", graph_dict=graph_dict)
    assert result == {"A", "B", "C"}

    # Starting from X should return only X, Y
    result = utils.filter_vertices_from_vertex(vertices_ids, "X", graph_dict=graph_dict)
    assert result == {"X", "Y"}

    # Test case 4: Invalid vertex
    result = utils.filter_vertices_from_vertex(vertices_ids, "Z", graph_dict=graph_dict)
    assert result == set()

    # Test case 5: Using callback functions instead of graph_dict
    def get_successors(v: str) -> list[str]:
        return graph_dict[v]["successors"]

    def get_predecessors(v: str) -> list[str]:
        return graph_dict[v]["predecessors"]

    result = utils.filter_vertices_from_vertex(
        vertices_ids,
        "A",
        get_vertex_predecessors=get_predecessors,
        get_vertex_successors=get_successors,
    )
    assert result == {"A", "B", "C"}