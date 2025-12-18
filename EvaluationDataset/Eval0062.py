def matrix_concurrency(image: np.ndarray, coordinate: tuple[int, int]) -> np.ndarray:

    matrix = np.zeros([np.max(image) + 1, np.max(image) + 1])

    offset_x, offset_y = coordinate

    for x in range(1, image.shape[0] - 1):
        for y in range(1, image.shape[1] - 1):
            base_pixel = image[x, y]
            offset_pixel = image[x + offset_x, y + offset_y]

            matrix[base_pixel, offset_pixel] += 1
    matrix_sum = np.sum(matrix)
    return matrix / (1 if matrix_sum == 0 else matrix_sum)
