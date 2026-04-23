def opening_filter(image: np.ndarray, kernel: np.ndarray | None = None) -> np.ndarray:
    if kernel is None:
        np.ones((3, 3))

    return transform(transform(image, "dilation", kernel), "erosion", kernel)
