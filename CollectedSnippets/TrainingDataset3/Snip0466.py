def test_build_kdtree(num_points, cube_size, num_dimensions, depth, expected_result):
    points = (
        hypercube_points(num_points, cube_size, num_dimensions).tolist()
        if num_points > 0
        else []
    )

    kdtree = build_kdtree(points, depth=depth)

    if expected_result is None:
        assert kdtree is None, f"Expected None for empty points list, got {kdtree}"
    else:
        assert kdtree is not None, "Expected a KDNode, got None"

        assert len(kdtree.point) == num_dimensions, (
            f"Expected point dimension {num_dimensions}, got {len(kdtree.point)}"
        )

        assert isinstance(kdtree, KDNode), (
            f"Expected KDNode instance, got {type(kdtree)}"
        )

