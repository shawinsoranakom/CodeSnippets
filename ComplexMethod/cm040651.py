def _load_image_tf(
    path,
    image_size,
    num_channels,
    interpolation,
    data_format,
    crop_to_aspect_ratio=False,
    pad_to_aspect_ratio=False,
):
    """Load an image from a path and resize it."""
    img = tf.io.read_file(path)
    img = tf.image.decode_image(
        img, channels=num_channels, expand_animations=False
    )

    if pad_to_aspect_ratio and crop_to_aspect_ratio:
        raise ValueError(
            "Only one of `pad_to_aspect_ratio`, `crop_to_aspect_ratio`"
            " can be set to `True`."
        )

    if crop_to_aspect_ratio:
        from keras.src.backend import tensorflow as tf_backend

        if data_format == "channels_first":
            img = tf.transpose(img, (2, 0, 1))
        img = image_utils.smart_resize(
            img,
            image_size,
            interpolation=interpolation,
            data_format=data_format,
            backend_module=tf_backend,
        )
    elif pad_to_aspect_ratio:
        img = tf.image.resize_with_pad(
            img, image_size[0], image_size[1], method=interpolation
        )
        if data_format == "channels_first":
            img = tf.transpose(img, (2, 0, 1))
    else:
        img = tf.image.resize(img, image_size, method=interpolation)
        if data_format == "channels_first":
            img = tf.transpose(img, (2, 0, 1))

    if data_format == "channels_last":
        img.set_shape((image_size[0], image_size[1], num_channels))
    else:
        img.set_shape((num_channels, image_size[0], image_size[1]))
    return img