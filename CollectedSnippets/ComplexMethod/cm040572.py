def _perspective_transform_numpy(
    images,
    start_points,
    end_points,
    interpolation="bilinear",
    fill_value=0,
    data_format=None,
):
    data_format = backend.standardize_data_format(data_format)

    need_squeeze = False
    if len(images.shape) == 3:
        images = np.expand_dims(images, axis=0)
        need_squeeze = True

    if len(start_points.shape) == 2:
        start_points = np.expand_dims(start_points, axis=0)
    if len(end_points.shape) == 2:
        end_points = np.expand_dims(end_points, axis=0)

    if data_format == "channels_first":
        images = np.transpose(images, (0, 2, 3, 1))

    batch_size, height, width, channels = images.shape

    transforms = _compute_homography_matrix(start_points, end_points)

    if len(transforms.shape) == 1:
        transforms = np.expand_dims(transforms, axis=0)
    if transforms.shape[0] == 1 and batch_size > 1:
        transforms = np.tile(transforms, (batch_size, 1))

    x, y = np.meshgrid(
        np.arange(width, dtype=np.float32),
        np.arange(height, dtype=np.float32),
        indexing="xy",
    )

    output = np.empty((batch_size, height, width, channels))

    for i in range(batch_size):
        a0, a1, a2, a3, a4, a5, a6, a7 = transforms[i]
        denom = a6 * x + a7 * y + 1.0
        x_in = (a0 * x + a1 * y + a2) / denom
        y_in = (a3 * x + a4 * y + a5) / denom

        coords = np.stack([y_in.ravel(), x_in.ravel()], axis=0)

        mapped_channels = []
        for channel in range(channels):
            channel_img = images[i, :, :, channel]

            mapped_channel = _fixed_map_coordinates(
                channel_img,
                coords,
                order=AFFINE_TRANSFORM_INTERPOLATIONS[interpolation],
                fill_mode="constant",
                fill_value=fill_value,
            )
            mapped_channels.append(mapped_channel.reshape(height, width))

        output[i] = np.stack(mapped_channels, axis=-1)

    if data_format == "channels_first":
        output = np.transpose(output, (0, 3, 1, 2))
    if need_squeeze:
        output = np.squeeze(output, axis=0)

    return output