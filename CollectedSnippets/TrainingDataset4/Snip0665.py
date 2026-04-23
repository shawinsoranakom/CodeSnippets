def get_neighbors_pixel(
    image: np.ndarray, x_coordinate: int, y_coordinate: int, center: int
) -> int:

    try:
        return int(image[x_coordinate][y_coordinate] >= center)
    except (IndexError, TypeError):
        return 0
