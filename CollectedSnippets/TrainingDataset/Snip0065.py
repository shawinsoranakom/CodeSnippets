def get_bounds(
    fft_results: np.ndarray, samplerate: int
) -> tuple[int | float, int | float]:
    
    lowest = min([-20, np.min(fft_results[1 : samplerate // 2 - 1])])
    highest = max([20, np.max(fft_results[1 : samplerate // 2 - 1])])
    return lowest, highest
