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
    if interpolation not in AFFINE_TRANSFORM_INTERPOLATIONS.keys():
        raise ValueError(
            "Invalid value for argument `interpolation`. Expected of one "
            f"{set(AFFINE_TRANSFORM_INTERPOLATIONS.keys())}. Received: "
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
    alpha = convert_to_tensor(alpha)
    sigma = convert_to_tensor(sigma)
    input_dtype = images.dtype
    kernel_size = (int(6 * sigma) | 1, int(6 * sigma) | 1)

    need_squeeze = False
    if len(images.shape) == 3:
        images = jnp.expand_dims(images, axis=0)
        need_squeeze = True

    if data_format == "channels_last":
        batch_size, height, width, channels = images.shape
        channel_axis = -1
    else:
        batch_size, channels, height, width = images.shape
        channel_axis = 1

    seed = draw_seed(seed)
    dx = (
        jax.random.normal(
            seed, shape=(batch_size, height, width), dtype=input_dtype
        )
        * sigma
    )
    dy = (
        jax.random.normal(
            seed, shape=(batch_size, height, width), dtype=input_dtype
        )
        * sigma
    )

    dx = gaussian_blur(
        jnp.expand_dims(dx, axis=channel_axis),
        kernel_size=kernel_size,
        sigma=(sigma, sigma),
        data_format=data_format,
    )
    dy = gaussian_blur(
        jnp.expand_dims(dy, axis=channel_axis),
        kernel_size=kernel_size,
        sigma=(sigma, sigma),
        data_format=data_format,
    )

    dx = jnp.squeeze(dx)
    dy = jnp.squeeze(dy)

    x, y = jnp.meshgrid(jnp.arange(width), jnp.arange(height))
    x, y = x[None, :, :], y[None, :, :]

    distorted_x = x + alpha * dx
    distorted_y = y + alpha * dy

    transformed_images = jnp.zeros_like(images)

    if data_format == "channels_last":
        for i in range(channels):
            transformed_images = transformed_images.at[..., i].set(
                jnp.stack(
                    [
                        map_coordinates(
                            images[b, ..., i],
                            [distorted_y[b], distorted_x[b]],
                            order=AFFINE_TRANSFORM_INTERPOLATIONS[
                                interpolation
                            ],
                            fill_mode=fill_mode,
                            fill_value=fill_value,
                        )
                        for b in range(batch_size)
                    ]
                )
            )
    else:
        for i in range(channels):
            transformed_images = transformed_images.at[:, i, :, :].set(
                jnp.stack(
                    [
                        map_coordinates(
                            images[b, i, ...],
                            [distorted_y[b], distorted_x[b]],
                            order=AFFINE_TRANSFORM_INTERPOLATIONS[
                                interpolation
                            ],
                            fill_mode=fill_mode,
                            fill_value=fill_value,
                        )
                        for b in range(batch_size)
                    ]
                )
            )

    if need_squeeze:
        transformed_images = jnp.squeeze(transformed_images, axis=0)
    transformed_images = transformed_images.astype(input_dtype)

    return transformed_images