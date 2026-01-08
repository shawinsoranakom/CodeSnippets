def test_edge_cases():
    empty_kdtree = build_kdtree([])
    query_point = [0.0] * 2

    nearest_point, nearest_dist, nodes_visited = nearest_neighbour_search(
        empty_kdtree, query_point
    )

    assert nearest_point is None
    assert nearest_dist == float("inf")
    assert nodes_visited == 0
