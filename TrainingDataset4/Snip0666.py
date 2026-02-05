def local_binary_value(image: np.ndarray, x_coordinate: int, y_coordinate: int) -> int:
    center = image[x_coordinate][y_coordinate]
    powers = [1, 2, 4, 8, 16, 32, 64, 128]

    if center is None:
        return 0

    binary_values = [
        get_neighbors_pixel(image, x_coordinate - 1, y_coordinate + 1, center),
        get_neighbors_pixel(image, x_coordinate, y_coordinate + 1, center),
        get_neighbors_pixel(image, x_coordinate - 1, y_coordinate, center),
        get_neighbors_pixel(image, x_coordinate + 1, y_coordinate + 1, center),
        get_neighbors_pixel(image, x_coordinate + 1, y_coordinate, center),
        get_neighbors_pixel(image, x_coordinate + 1, y_coordinate - 1, center),
        get_neighbors_pixel(image, x_coordinate, y_coordinate - 1, center),
        get_neighbors_pixel(image, x_coordinate - 1, y_coordinate - 1, center),
    ]

    return sum(
        binary_value * power for binary_value, power in zip(binary_values, powers)
    )
