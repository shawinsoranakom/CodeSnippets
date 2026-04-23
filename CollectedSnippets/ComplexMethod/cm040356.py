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
    target_height, target_width = size
    if len(images.shape) == 4:
        if data_format == "channels_last":
            size = (images.shape[0],) + size + (images.shape[-1],)
        else:
            size = (images.shape[0], images.shape[1]) + size
        batch_size = images.shape[0]
    elif len(images.shape) == 3:
        if data_format == "channels_last":
            size = size + (images.shape[-1],)
        else:
            size = (images.shape[0],) + size
    else:
        raise ValueError(
            "Invalid images rank: expected rank 3 (single image) "
            "or rank 4 (batch of images). Received input with shape: "
            f"images.shape={images.shape}"
        )

    if crop_to_aspect_ratio:
        shape = images.shape
        if data_format == "channels_last":
            height, width = shape[-3], shape[-2]
        else:
            height, width = shape[-2], shape[-1]
        crop_height = int(float(width * target_height) / target_width)
        crop_height = max(min(height, crop_height), 1)
        crop_width = int(float(height * target_width) / target_height)
        crop_width = max(min(width, crop_width), 1)
        crop_box_hstart = int(float(height - crop_height) / 2)
        crop_box_wstart = int(float(width - crop_width) / 2)
        if data_format == "channels_last":
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
        else:
            if len(images.shape) == 4:
                images = images[
                    :,
                    :,
                    crop_box_hstart : crop_box_hstart + crop_height,
                    crop_box_wstart : crop_box_wstart + crop_width,
                ]
            else:
                images = images[
                    :,
                    crop_box_hstart : crop_box_hstart + crop_height,
                    crop_box_wstart : crop_box_wstart + crop_width,
                ]
    elif pad_to_aspect_ratio:
        shape = images.shape
        if data_format == "channels_last":
            height, width, channels = shape[-3], shape[-2], shape[-1]
        else:
            height, width, channels = shape[-2], shape[-1], shape[-3]

        pad_height = int(float(width * target_height) / target_width)
        pad_height = max(height, pad_height)
        pad_width = int(float(height * target_width) / target_height)
        pad_width = max(width, pad_width)
        img_box_hstart = int(float(pad_height - height) / 2)
        img_box_wstart = int(float(pad_width - width) / 2)
        if data_format == "channels_last":
            if img_box_hstart > 0:
                if len(images.shape) == 4:
                    padded_img = jnp.concatenate(
                        [
                            jnp.ones(
                                (batch_size, img_box_hstart, width, channels),
                                dtype=images.dtype,
                            )
                            * fill_value,
                            images,
                            jnp.ones(
                                (batch_size, img_box_hstart, width, channels),
                                dtype=images.dtype,
                            )
                            * fill_value,
                        ],
                        axis=1,
                    )
                else:
                    padded_img = jnp.concatenate(
                        [
                            jnp.ones(
                                (img_box_hstart, width, channels),
                                dtype=images.dtype,
                            )
                            * fill_value,
                            images,
                            jnp.ones(
                                (img_box_hstart, width, channels),
                                dtype=images.dtype,
                            )
                            * fill_value,
                        ],
                        axis=0,
                    )
            elif img_box_wstart > 0:
                if len(images.shape) == 4:
                    padded_img = jnp.concatenate(
                        [
                            jnp.ones(
                                (batch_size, height, img_box_wstart, channels),
                                dtype=images.dtype,
                            )
                            * fill_value,
                            images,
                            jnp.ones(
                                (batch_size, height, img_box_wstart, channels),
                                dtype=images.dtype,
                            )
                            * fill_value,
                        ],
                        axis=2,
                    )
                else:
                    padded_img = jnp.concatenate(
                        [
                            jnp.ones(
                                (height, img_box_wstart, channels),
                                dtype=images.dtype,
                            )
                            * fill_value,
                            images,
                            jnp.ones(
                                (height, img_box_wstart, channels),
                                dtype=images.dtype,
                            )
                            * fill_value,
                        ],
                        axis=1,
                    )
            else:
                padded_img = images
        else:
            if img_box_hstart > 0:
                if len(images.shape) == 4:
                    padded_img = jnp.concatenate(
                        [
                            jnp.ones(
                                (batch_size, channels, img_box_hstart, width)
                            )
                            * fill_value,
                            images,
                            jnp.ones(
                                (batch_size, channels, img_box_hstart, width)
                            )
                            * fill_value,
                        ],
                        axis=2,
                    )
                else:
                    padded_img = jnp.concatenate(
                        [
                            jnp.ones((channels, img_box_hstart, width))
                            * fill_value,
                            images,
                            jnp.ones((channels, img_box_hstart, width))
                            * fill_value,
                        ],
                        axis=1,
                    )
            elif img_box_wstart > 0:
                if len(images.shape) == 4:
                    padded_img = jnp.concatenate(
                        [
                            jnp.ones(
                                (batch_size, channels, height, img_box_wstart)
                            )
                            * fill_value,
                            images,
                            jnp.ones(
                                (batch_size, channels, height, img_box_wstart)
                            )
                            * fill_value,
                        ],
                        axis=3,
                    )
                else:
                    padded_img = jnp.concatenate(
                        [
                            jnp.ones((channels, height, img_box_wstart))
                            * fill_value,
                            images,
                            jnp.ones((channels, height, img_box_wstart))
                            * fill_value,
                        ],
                        axis=2,
                    )
            else:
                padded_img = images
        images = padded_img

    return jax.image.resize(
        images, size, method=interpolation, antialias=antialias
    )