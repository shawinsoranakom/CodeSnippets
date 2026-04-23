def gabor_filter_kernel(
    ksize: int, sigma: int, theta: int, lambd: int, gamma: int, psi: int
) -> np.ndarray:
    if (ksize % 2) == 0:
        ksize = ksize + 1
    gabor = np.zeros((ksize, ksize), dtype=np.float32)

    for y in range(ksize):
        for x in range(ksize):
            px = x - ksize // 2
            py = y - ksize // 2
            _theta = theta / 180 * np.pi
            cos_theta = np.cos(_theta)
            sin_theta = np.sin(_theta)
            _x = cos_theta * px + sin_theta * py

            _y = -sin_theta * px + cos_theta * py

            gabor[y, x] = np.exp(-(_x**2 + gamma**2 * _y**2) / (2 * sigma**2)) * np.cos(
                2 * np.pi * _x / lambd + psi
            )

    return gabor


