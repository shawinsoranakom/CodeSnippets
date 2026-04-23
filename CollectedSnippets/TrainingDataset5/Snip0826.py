def iteration_step(vectors: list[np.ndarray]) -> list[np.ndarray]:
    new_vectors = []
    for i, start_vector in enumerate(vectors[:-1]):
        end_vector = vectors[i + 1]
        new_vectors.append(start_vector)
        difference_vector = end_vector - start_vector
        new_vectors.append(start_vector + difference_vector / 3)
        new_vectors.append(
            start_vector + difference_vector / 3 + rotate(difference_vector / 3, 60)
        )
        new_vectors.append(start_vector + difference_vector * 2 / 3)
    new_vectors.append(vectors[-1])
    return new_vectors
