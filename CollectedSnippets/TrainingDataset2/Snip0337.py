def main() -> None:
    num_points: int = 5000
    cube_size: float = 10.0 
    num_dimensions: int = 10

    points: np.ndarray = hypercube_points(num_points, cube_size, num_dimensions)
    hypercube_kdtree = build_kdtree(points.tolist())

    rng = np.random.default_rng()
    query_point: list[float] = rng.random(num_dimensions).tolist()

    nearest_point, nearest_dist, nodes_visited = nearest_neighbour_search(
        hypercube_kdtree, query_point
    )

    print(f"Query point: {query_point}")
    print(f"Nearest point: {nearest_point}")
    print(f"Distance: {nearest_dist:.4f}")
    print(f"Nodes visited: {nodes_visited}")
