def get_distances(descriptors: np.ndarray, base: int) -> list[tuple[int, float]]:

    distances = np.array(
        [euclidean(descriptor, descriptors[base]) for descriptor in descriptors]
    )
    normalized_distances: list[float] = normalize_array(distances, 1).tolist()
    enum_distances = list(enumerate(normalized_distances))
    enum_distances.sort(key=lambda tup: tup[1], reverse=True)
    return enum_distances
