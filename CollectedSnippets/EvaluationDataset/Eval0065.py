def euclidean(point_1: np.ndarray, point_2: np.ndarray) -> float:

    return float(np.sqrt(np.sum(np.square(point_1 - point_2))))
