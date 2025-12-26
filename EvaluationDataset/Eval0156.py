def peak_signal_to_noise_ratio(original: float, contrast: float) -> float:
    mse = np.mean((original - contrast) ** 2)
    if mse == 0:
        return 100

    return 20 * math.log10(PIXEL_MAX / math.sqrt(mse))
