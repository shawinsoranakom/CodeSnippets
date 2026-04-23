def elastic_transform_np(
    images,
    alpha=20.0,
    sigma=5.0,
    interpolation="bilinear",
    fill_mode="reflect",
    fill_value=0.0,
    seed=None,
    data_format=None,
):
    data_format = backend.standardize_data_format(data_format)

    images = np.asarray(images)
    input_dtype = images.dtype

    alpha = np.asarray(alpha, dtype=input_dtype)
    sigma = np.asarray(sigma, dtype=input_dtype)

    kernel_size = (int(6 * sigma) | 1, int(6 * sigma) | 1)

    need_squeeze = False
    if len(images.shape) == 3:
        images = np.expand_dims(images, axis=0)
        need_squeeze = True

    if data_format == "channels_last":
        batch_size, height, width, channels = images.shape
        channel_axis = -1
    else:
        batch_size, channels, height, width = images.shape
        channel_axis = 1

    rng = np.random.default_rng([seed, 0])
    dx = (
        rng.normal(size=(batch_size, height, width), loc=0.0, scale=1.0).astype(
            input_dtype
        )
        * sigma
    )
    dy = (
        rng.normal(size=(batch_size, height, width), loc=0.0, scale=1.0).astype(
            input_dtype
        )
        * sigma
    )

    dx = gaussian_blur_np(
        np.expand_dims(dx, axis=channel_axis),
        kernel_size=kernel_size,
        sigma=(sigma, sigma),
        data_format=data_format,
    )
    dy = gaussian_blur_np(
        np.expand_dims(dy, axis=channel_axis),
        kernel_size=kernel_size,
        sigma=(sigma, sigma),
        data_format=data_format,
    )

    dx = np.squeeze(dx)
    dy = np.squeeze(dy)

    x, y = np.meshgrid(np.arange(width), np.arange(height))
    x, y = x[None, :, :], y[None, :, :]

    distorted_x = x + alpha * dx
    distorted_y = y + alpha * dy

    transformed_images = np.zeros_like(images)

    if data_format == "channels_last":
        for i in range(channels):
            transformed_images[..., i] = np.stack(
                [
                    _fixed_map_coordinates(
                        images[b, ..., i],
                        [distorted_y[b], distorted_x[b]],
                        order=AFFINE_TRANSFORM_INTERPOLATIONS[interpolation],
                        fill_mode=fill_mode,
                        fill_value=fill_value,
                    )
                    for b in range(batch_size)
                ]
            )
    else:
        for i in range(channels):
            transformed_images[:, i, :, :] = np.stack(
                [
                    _fixed_map_coordinates(
                        images[b, i, ...],
                        [distorted_y[b], distorted_x[b]],
                        order=AFFINE_TRANSFORM_INTERPOLATIONS[interpolation],
                        fill_mode=fill_mode,
                        fill_value=fill_value,
                    )
                    for b in range(batch_size)
                ]
            )

    if need_squeeze:
        transformed_images = np.squeeze(transformed_images, axis=0)
    transformed_images = transformed_images.astype(input_dtype)

    return transformed_images