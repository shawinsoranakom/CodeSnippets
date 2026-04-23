def my_laplacian(src: np.ndarray, ksize: int) -> np.ndarray:
    kernels = {
        1: np.array([[0, -1, 0], [-1, 4, -1], [0, -1, 0]]),
        3: np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]]),
        5: np.array(
            [
                [0, 0, -1, 0, 0],
                [0, -1, -2, -1, 0],
                [-1, -2, 16, -2, -1],
                [0, -1, -2, -1, 0],
                [0, 0, -1, 0, 0],
            ]
        ),
        7: np.array(
            [
                [0, 0, 0, -1, 0, 0, 0],
                [0, 0, -2, -3, -2, 0, 0],
                [0, -2, -7, -10, -7, -2, 0],
                [-1, -3, -10, 68, -10, -3, -1],
                [0, -2, -7, -10, -7, -2, 0],
                [0, 0, -2, -3, -2, 0, 0],
                [0, 0, 0, -1, 0, 0, 0],
            ]
        ),
    }
    if ksize not in kernels:
        msg = f"ksize must be in {tuple(kernels)}"
        raise ValueError(msg)

    return filter2D(
        src, CV_64F, kernels[ksize], 0, borderType=BORDER_DEFAULT, anchor=(0, 0)
    )
