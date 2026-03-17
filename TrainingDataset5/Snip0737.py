def test_local_binary_pattern():
    from os import getenv 

    file_name = "lena_small.jpg" if getenv("CI") else "lena.jpg"
    file_path = f"digital_image_processing/image_data/{file_name}"

    image = imread(file_path, 0)

    x_coordinate = 0
    y_coordinate = 0
    center = image[x_coordinate][y_coordinate]

    neighbors_pixels = lbp.get_neighbors_pixel(
        image, x_coordinate, y_coordinate, center
    )

    assert neighbors_pixels is not None

    lbp_image = np.zeros((image.shape[0], image.shape[1]))

    for i in range(image.shape[0]):
        for j in range(image.shape[1]):
            lbp_image[i][j] = lbp.local_binary_value(image, i, j)

    assert lbp_image.any()
