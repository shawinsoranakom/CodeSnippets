def hypercube_points(
    num_points: int, hypercube_size: float, num_dimensions: int
) -> np.ndarray:
    rng = np.random.default_rng()
    shape = (num_points, num_dimensions)
    return hypercube_size * rng.random(shape)
