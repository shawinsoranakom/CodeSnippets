def normalize_image(
    image: np.ndarray, cap: float = 255.0, data_type: np.dtype = np.uint8
) -> np.ndarray:
    normalized = (image - np.min(image)) / (np.max(image) - np.min(image)) * cap
    return normalized.astype(data_type)
