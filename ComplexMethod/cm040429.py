def hsv_to_rgb(images, data_format=None):
    images = convert_to_tensor(images)
    dtype = images.dtype
    data_format = backend.standardize_data_format(data_format)
    if len(images.shape) not in (3, 4):
        raise ValueError(
            "Invalid images rank: expected rank 3 (single image) "
            "or rank 4 (batch of images). Received input with shape: "
            f"images.shape={images.shape}"
        )
    if not backend.is_float_dtype(dtype):
        raise ValueError(
            "Invalid images dtype: expected float dtype. "
            f"Received: images.dtype={backend.standardize_dtype(dtype)}"
        )
    if data_format == "channels_first":
        if len(images.shape) == 4:
            images = tf.transpose(images, (0, 2, 3, 1))
        else:
            images = tf.transpose(images, (1, 2, 0))
    images = tf.image.hsv_to_rgb(images)
    if data_format == "channels_first":
        if len(images.shape) == 4:
            images = tf.transpose(images, (0, 3, 1, 2))
        elif len(images.shape) == 3:
            images = tf.transpose(images, (2, 0, 1))
    return images