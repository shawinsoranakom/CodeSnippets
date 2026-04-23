def perspective_transform(
    images,
    start_points,
    end_points,
    interpolation="bilinear",
    fill_value=0,
    data_format=None,
):
    data_format = backend.standardize_data_format(data_format)
    start_points = convert_to_tensor(start_points, dtype=tf.float32)
    end_points = convert_to_tensor(end_points, dtype=tf.float32)

    if interpolation not in AFFINE_TRANSFORM_INTERPOLATIONS:
        raise ValueError(
            "Invalid value for argument `interpolation`. Expected of one "
            f"{AFFINE_TRANSFORM_INTERPOLATIONS}. Received: "
            f"interpolation={interpolation}"
        )
    if len(images.shape) not in (3, 4):
        raise ValueError(
            "Invalid images rank: expected rank 3 (single image) "
            "or rank 4 (batch of images). Received input with shape: "
            f"images.shape={images.shape}"
        )

    if start_points.shape.rank not in (2, 3) or start_points.shape[-2:] != (
        4,
        2,
    ):
        raise ValueError(
            "Invalid start_points shape: expected (4,2) for a single image"
            f" or (N,4,2) for a batch. Received shape: {start_points.shape}"
        )
    if end_points.shape.rank not in (2, 3) or end_points.shape[-2:] != (4, 2):
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
        images = tf.expand_dims(images, axis=0)
        need_squeeze = True

    if len(start_points.shape) == 2:
        start_points = tf.expand_dims(start_points, axis=0)
    if len(end_points.shape) == 2:
        end_points = tf.expand_dims(end_points, axis=0)

    if data_format == "channels_first":
        images = tf.transpose(images, (0, 2, 3, 1))

    transform = compute_homography_matrix(start_points, end_points)
    if len(transform.shape) == 1:
        transform = tf.expand_dims(transform, axis=0)

    output = tf.raw_ops.ImageProjectiveTransformV3(
        images=images,
        transforms=tf.cast(transform, dtype=tf.float32),
        output_shape=tf.shape(images)[1:-1],
        fill_value=fill_value,
        interpolation=interpolation.upper(),
    )
    output = tf.ensure_shape(output, images.shape)

    if data_format == "channels_first":
        output = tf.transpose(output, (0, 3, 1, 2))
    if need_squeeze:
        output = tf.squeeze(output, axis=0)
    return output