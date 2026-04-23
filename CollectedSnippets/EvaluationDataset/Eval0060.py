def closing_filter(image: np.ndarray, kernel: np.ndarray | None = None) -> np.ndarray:
    if kernel is None:
        kernel = np.ones((3, 3))
    return transform(transform(image, "erosion", kernel), "dilation", kernel)
