def transform(
    image: np.ndarray, kind: str, kernel: np.ndarray | None = None
) -> np.ndarray:
    if kernel is None:
        kernel = np.ones((3, 3))

    if kind == "erosion":
        constant = 1
        apply = np.max
    else:
        constant = 0
        apply = np.min

    center_x, center_y = (x // 2 for x in kernel.shape)
    transformed = np.zeros(image.shape, dtype=np.uint8)
    padded = np.pad(image, 1, "constant", constant_values=constant)

    for x in range(center_x, padded.shape[0] - center_x):
        for y in range(center_y, padded.shape[1] - center_y):
            center = padded[
                x - center_x : x + center_x + 1, y - center_y : y + center_y + 1
            ]
            transformed[x - center_x, y - center_y] = apply(center[kernel == 1])

    return transformed
