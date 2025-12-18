def grayscale(image: np.ndarray) -> np.ndarray:

    return np.dot(image[:, :, 0:3], [0.299, 0.587, 0.114]).astype(np.uint8)
