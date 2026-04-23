def perspective_transform(
    images,
    start_points,
    end_points,
    interpolation="bilinear",
    fill_value=0,
    data_format=None,
):
    data_format = backend.standardize_data_format(data_format)
    if interpolation not in AFFINE_TRANSFORM_INTERPOLATIONS.keys():
        raise ValueError(
            "Invalid value for argument `interpolation`. Expected of one "
            f"{set(AFFINE_TRANSFORM_INTERPOLATIONS.keys())}. Received: "
            f"interpolation={interpolation}"
        )

    if len(images.shape) not in (3, 4):
        raise ValueError(
            "Invalid images rank: expected rank 3 (single image) "
            "or rank 4 (batch of images). Received input with shape: "
            f"images.shape={images.shape}"
        )

    if start_points.shape[-2:] != (4, 2) or start_points.ndim not in (2, 3):
        raise ValueError(
            "Invalid start_points shape: expected (4,2) for a single image"
            f" or (N,4,2) for a batch. Received shape: {start_points.shape}"
        )
    if end_points.shape[-2:] != (4, 2) or end_points.ndim not in (2, 3):
        raise ValueError(
            "Invalid end_points shape: expected (4,2) for a single image"
            f" or (N,4,2) for a batch. Received shape: {end_points.shape}"
        )
    if start_points.shape != end_points.shape:
        raise ValueError(
            "start_points and end_points must have the same shape."
            f" Received start_points.shape={start_points.shape}, "
            f"end_points.shape={end_points.shape}"
        )

    need_squeeze = False
    if len(images.shape) == 3:
        images = jnp.expand_dims(images, axis=0)
        need_squeeze = True

    if len(start_points.shape) == 2:
        start_points = jnp.expand_dims(start_points, axis=0)
    if len(end_points.shape) == 2:
        end_points = jnp.expand_dims(end_points, axis=0)

    if data_format == "channels_first":
        images = jnp.transpose(images, (0, 2, 3, 1))

    _, height, width, _ = images.shape
    transforms = compute_homography_matrix(
        jnp.asarray(start_points, dtype="float32"),
        jnp.asarray(end_points, dtype="float32"),
    )

    x, y = jnp.meshgrid(jnp.arange(width), jnp.arange(height), indexing="xy")
    grid = jnp.stack([x.ravel(), y.ravel(), jnp.ones_like(x).ravel()], axis=0)

    def transform_coordinates(transform):
        denom = transform[6] * grid[0] + transform[7] * grid[1] + 1.0
        x_in = (
            transform[0] * grid[0] + transform[1] * grid[1] + transform[2]
        ) / denom
        y_in = (
            transform[3] * grid[0] + transform[4] * grid[1] + transform[5]
        ) / denom
        return jnp.stack([y_in, x_in], axis=0)

    transformed_coords = jax.vmap(transform_coordinates)(transforms)

    def interpolate_image(image, coords):
        def interpolate_channel(channel_img):
            return jax.scipy.ndimage.map_coordinates(
                channel_img,
                coords,
                order=AFFINE_TRANSFORM_INTERPOLATIONS[interpolation],
                mode="constant",
                cval=fill_value,
            ).reshape(height, width)

        return jax.vmap(interpolate_channel, in_axes=0)(
            jnp.moveaxis(image, -1, 0)
        )

    output = jax.vmap(interpolate_image, in_axes=(0, 0))(
        images, transformed_coords
    )
    output = jnp.moveaxis(output, 1, -1)

    if data_format == "channels_first":
        output = jnp.transpose(output, (0, 3, 1, 2))
    if need_squeeze:
        output = jnp.squeeze(output, axis=0)

    return output