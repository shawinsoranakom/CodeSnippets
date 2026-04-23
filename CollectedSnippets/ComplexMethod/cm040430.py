def resize(
    images,
    size,
    interpolation="bilinear",
    antialias=False,
    crop_to_aspect_ratio=False,
    pad_to_aspect_ratio=False,
    fill_mode="constant",
    fill_value=0.0,
    data_format=None,
):
    data_format = backend.standardize_data_format(data_format)
    if interpolation not in RESIZE_INTERPOLATIONS:
        raise ValueError(
            "Invalid value for argument `interpolation`. Expected of one "
            f"{RESIZE_INTERPOLATIONS}. Received: interpolation={interpolation}"
        )
    if fill_mode != "constant":
        raise ValueError(
            "Invalid value for argument `fill_mode`. Only `'constant'` "
            f"is supported. Received: fill_mode={fill_mode}"
        )
    if pad_to_aspect_ratio and crop_to_aspect_ratio:
        raise ValueError(
            "Only one of `pad_to_aspect_ratio` & `crop_to_aspect_ratio` "
            "can be `True`."
        )
    if not len(size) == 2:
        raise ValueError(
            "Argument `size` must be a tuple of two elements "
            f"(height, width). Received: size={size}"
        )
    size = tuple(size)
    if len(images.shape) not in (3, 4):
        raise ValueError(
            "Invalid images rank: expected rank 3 (single image) "
            "or rank 4 (batch of images). Received input with shape: "
            f"images.shape={images.shape}"
        )
    if data_format == "channels_first":
        if len(images.shape) == 4:
            images = tf.transpose(images, (0, 2, 3, 1))
        else:
            images = tf.transpose(images, (1, 2, 0))

    if crop_to_aspect_ratio:
        shape = tf.shape(images)
        height, width = shape[-3], shape[-2]
        target_height, target_width = size
        crop_height = tf.cast(
            tf.cast(width * target_height, "float32") / target_width,
            "int32",
        )
        crop_height = tf.maximum(tf.minimum(height, crop_height), 1)
        crop_height = tf.cast(crop_height, "int32")
        crop_width = tf.cast(
            tf.cast(height * target_width, "float32") / target_height,
            "int32",
        )
        crop_width = tf.maximum(tf.minimum(width, crop_width), 1)
        crop_width = tf.cast(crop_width, "int32")

        crop_box_hstart = tf.cast(
            tf.cast(height - crop_height, "float32") / 2, "int32"
        )
        crop_box_wstart = tf.cast(
            tf.cast(width - crop_width, "float32") / 2, "int32"
        )
        if len(images.shape) == 4:
            images = images[
                :,
                crop_box_hstart : crop_box_hstart + crop_height,
                crop_box_wstart : crop_box_wstart + crop_width,
                :,
            ]
        else:
            images = images[
                crop_box_hstart : crop_box_hstart + crop_height,
                crop_box_wstart : crop_box_wstart + crop_width,
                :,
            ]
    elif pad_to_aspect_ratio:
        shape = tf.shape(images)
        height, width = shape[-3], shape[-2]
        target_height, target_width = size
        pad_height = tf.cast(
            tf.cast(width * target_height, "float32") / target_width,
            "int32",
        )
        pad_height = tf.maximum(height, pad_height)
        pad_height = tf.cast(pad_height, "int32")
        pad_width = tf.cast(
            tf.cast(height * target_width, "float32") / target_height,
            "int32",
        )
        pad_width = tf.maximum(width, pad_width)
        pad_width = tf.cast(pad_width, "int32")

        img_box_hstart = tf.cast(
            tf.cast(pad_height - height, "float32") / 2, "int32"
        )
        img_box_wstart = tf.cast(
            tf.cast(pad_width - width, "float32") / 2, "int32"
        )
        if len(images.shape) == 4:
            batch_size = tf.shape(images)[0]
            channels = tf.shape(images)[3]
            padded_img = tf.cond(
                img_box_hstart > 0,
                lambda: tf.concat(
                    [
                        tf.ones(
                            (batch_size, img_box_hstart, width, channels),
                            dtype=images.dtype,
                        )
                        * fill_value,
                        images,
                        tf.ones(
                            (batch_size, img_box_hstart, width, channels),
                            dtype=images.dtype,
                        )
                        * fill_value,
                    ],
                    axis=1,
                ),
                lambda: images,
            )
            padded_img = tf.cond(
                img_box_wstart > 0,
                lambda: tf.concat(
                    [
                        tf.ones(
                            (batch_size, height, img_box_wstart, channels),
                            dtype=images.dtype,
                        )
                        * fill_value,
                        padded_img,
                        tf.ones(
                            (batch_size, height, img_box_wstart, channels),
                            dtype=images.dtype,
                        )
                        * fill_value,
                    ],
                    axis=2,
                ),
                lambda: padded_img,
            )
        else:
            channels = tf.shape(images)[2]
            padded_img = tf.cond(
                img_box_hstart > 0,
                lambda: tf.concat(
                    [
                        tf.ones(
                            (img_box_hstart, width, channels),
                            dtype=images.dtype,
                        )
                        * fill_value,
                        images,
                        tf.ones(
                            (img_box_hstart, width, channels),
                            dtype=images.dtype,
                        )
                        * fill_value,
                    ],
                    axis=0,
                ),
                lambda: images,
            )
            padded_img = tf.cond(
                img_box_wstart > 0,
                lambda: tf.concat(
                    [
                        tf.ones(
                            (height, img_box_wstart, channels),
                            dtype=images.dtype,
                        )
                        * fill_value,
                        padded_img,
                        tf.ones(
                            (height, img_box_wstart, channels),
                            dtype=images.dtype,
                        )
                        * fill_value,
                    ],
                    axis=1,
                ),
                lambda: padded_img,
            )
        images = padded_img

    resized = tf.image.resize(
        images, size, method=interpolation, antialias=antialias
    )
    if data_format == "channels_first":
        if len(images.shape) == 4:
            resized = tf.transpose(resized, (0, 3, 1, 2))
        elif len(images.shape) == 3:
            resized = tf.transpose(resized, (2, 0, 1))
    return resized