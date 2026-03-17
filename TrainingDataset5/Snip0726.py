def get_gauss_kernel(kernel_size: int, spatial_variance: float) -> np.ndarray:
    arr = np.zeros((kernel_size, kernel_size))
    for i in range(kernel_size):
        for j in range(kernel_size):
            arr[i, j] = math.sqrt(
                abs(i - kernel_size // 2) ** 2 + abs(j - kernel_size // 2) ** 2
            )
    return vec_gaussian(arr, spatial_variance)
