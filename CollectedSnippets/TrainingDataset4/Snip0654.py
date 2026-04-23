def vec_gaussian(img: np.ndarray, variance: float) -> np.ndarray:
    sigma = math.sqrt(variance)
    cons = 1 / (sigma * math.sqrt(2 * math.pi))
    return cons * np.exp(-((img / sigma) ** 2) * 0.5)
