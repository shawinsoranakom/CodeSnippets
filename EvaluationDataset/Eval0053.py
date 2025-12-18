def root_mean_square_error(original: np.ndarray, reference: np.ndarray) -> float:
    return float(np.sqrt(((original - reference) ** 2).mean()))
