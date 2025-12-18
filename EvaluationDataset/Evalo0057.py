def binarize(image: np.ndarray, threshold: float = 127.0) -> np.ndarray:
    return np.where(image > threshold, 1, 0)
