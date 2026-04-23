def elastic_transform(
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
    if interpolation not in AFFINE_TRANSFORM_INTERPOLATIONS:
        raise ValueError(
            "Invalid value for argument `interpolation`. Expected of one "
            f"{AFFINE_TRANSFORM_INTERPOLATIONS}. Received: "
            f"interpolation={interpolation}"
        )
    if fill_mode not in AFFINE_TRANSFORM_FILL_MODES:
        raise ValueError(
            "Invalid value for argument `fill_mode`. Expected of one "
            f"{AFFINE_TRANSFORM_FILL_MODES}. Received: fill_mode={fill_mode}"
        )
    if len(images.shape) not in (3, 4):
        raise ValueError(
            "Invalid images rank: expected rank 3 (single image) "
            "or rank 4 (batch of images). Received input with shape: "
            f"images.shape={images.shape}"
        )

    images = convert_to_tensor(images)
    input_dtype = images.dtype

    alpha = convert_to_tensor(alpha, dtype=input_dtype)
    sigma = convert_to_tensor(sigma, dtype=input_dtype)
    kernel_factor = convert_to_tensor(sigma, dtype="int32")
    kernel_size = (6 * kernel_factor | 1, 6 * kernel_factor | 1)

    need_squeeze = False
    if len(images.shape) == 3:
        images = tf.expand_dims(images, axis=0)
        need_squeeze = True

    if data_format == "channels_last":
        batch_size, height, width, channels = images.shape
        channel_axis = -1
    else:
        batch_size, channels, height, width = images.shape
        channel_axis = 1

    seed = draw_seed(seed)

    if batch_size is None:
        batch_size = 1

    dx = (
        tf.random.stateless_normal(
            shape=(batch_size, height, width),
            mean=0.0,
            stddev=1.0,
            dtype=input_dtype,
            seed=seed,
        )
        * sigma
    )
    dy = (
        tf.random.stateless_normal(
            shape=(batch_size, height, width),
            mean=0.0,
            stddev=1.0,
            dtype=input_dtype,
            seed=seed,
        )
        * sigma
    )

    dx = gaussian_blur(
        tf.expand_dims(dx, axis=channel_axis),
        kernel_size=kernel_size,
        sigma=(sigma, sigma),
        data_format=data_format,
    )
    dy = gaussian_blur(
        tf.expand_dims(dy, axis=channel_axis),
        kernel_size=kernel_size,
        sigma=(sigma, sigma),
        data_format=data_format,
    )

    dx = tf.squeeze(dx, axis=channel_axis)
    dy = tf.squeeze(dy, axis=channel_axis)

    x, y = tf.meshgrid(
        tf.range(width, dtype=input_dtype),
        tf.range(height, dtype=input_dtype),
        indexing="xy",
    )
    x = tf.expand_dims(x, axis=0)
    y = tf.expand_dims(y, axis=0)

    distorted_x = x + alpha * dx
    distorted_y = y + alpha * dy

    channel_outputs = []
    if data_format == "channels_last":
        for i in range(channels):
            channel_transformed = tf.stack(
                [
                    map_coordinates(
                        images[b, ..., i],
                        [distorted_y[b], distorted_x[b]],
                        order=AFFINE_TRANSFORM_INTERPOLATIONS.index(
                            interpolation
                        ),
                        fill_mode=fill_mode,
                        fill_value=fill_value,
                    )
                    for b in range(batch_size)
                ],
                axis=0,
            )
            channel_outputs.append(channel_transformed)
        transformed_images = tf.stack(channel_outputs, axis=-1)
    else:
        for i in range(channels):
            channel_transformed = tf.stack(
                [
                    map_coordinates(
                        images[b, i, ...],
                        [distorted_y[b], distorted_x[b]],
                        order=AFFINE_TRANSFORM_INTERPOLATIONS.index(
                            interpolation
                        ),
                        fill_mode=fill_mode,
                        fill_value=fill_value,
                    )
                    for b in range(batch_size)
                ],
                axis=0,
            )
            channel_outputs.append(channel_transformed)
        transformed_images = tf.stack(channel_outputs, axis=1)

    if need_squeeze:
        transformed_images = tf.squeeze(transformed_images, axis=0)
    transformed_images = tf.cast(transformed_images, input_dtype)

    return transformed_images