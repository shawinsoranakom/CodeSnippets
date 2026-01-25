def test_nearest_neighbour_search():
    num_points = 10
    cube_size = 10.0
    num_dimensions = 2
    points = hypercube_points(num_points, cube_size, num_dimensions)
    kdtree = build_kdtree(points.tolist())

    rng = np.random.default_rng()
    query_point = rng.random(num_dimensions).tolist()

    nearest_point, nearest_dist, nodes_visited = nearest_neighbour_search(
        kdtree, query_point
    )

    assert nearest_point is not None

    assert nearest_dist >= 0

    assert nodes_visited >= 0
