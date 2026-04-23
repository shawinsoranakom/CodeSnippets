def get_descriptors(
    masks: tuple[np.ndarray, np.ndarray], coordinate: tuple[int, int]
) -> np.ndarray:

    descriptors = np.array(
        [haralick_descriptors(matrix_concurrency(mask, coordinate)) for mask in masks]
    )

    return np.concatenate(descriptors, axis=None)

