def bilateral_filter(
    img: np.ndarray,
    spatial_variance: float,
    intensity_variance: float,
    kernel_size: int,
) -> np.ndarray:
    img2 = np.zeros(img.shape)
    gauss_ker = get_gauss_kernel(kernel_size, spatial_variance)
    size_x, size_y = img.shape
    for i in range(kernel_size // 2, size_x - kernel_size // 2):
        for j in range(kernel_size // 2, size_y - kernel_size // 2):
            img_s = get_slice(img, i, j, kernel_size)
            img_i = img_s - img_s[kernel_size // 2, kernel_size // 2]
            img_ig = vec_gaussian(img_i, intensity_variance)
            weights = np.multiply(gauss_ker, img_ig)
            vals = np.multiply(img_s, weights)
            val = np.sum(vals) / np.sum(weights)
            img2[i, j] = val
    return img2
