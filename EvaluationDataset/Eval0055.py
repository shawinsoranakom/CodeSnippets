def normalize_array(array: np.ndarray, cap: float = 1) -> np.ndarray:
    diff = np.max(array) - np.min(array)
    return (array - np.min(array)) / (1 if diff == 0 else diff) * cap
