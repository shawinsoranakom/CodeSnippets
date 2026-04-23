def _pad_images(
    images,
    top_padding,
    left_padding,
    bottom_padding,
    right_padding,
    target_height,
    target_width,
    data_format=None,
):
    data_format = backend.standardize_data_format(data_format)
    images = backend.convert_to_tensor(images)
    images_shape = ops.shape(images)

    # Check
    if len(images_shape) not in (3, 4):
        raise ValueError(
            f"Invalid shape for argument `images`: "
            "it must have rank 3 or 4. "
            f"Received: images.shape={images_shape}"
        )
    if [top_padding, bottom_padding, target_height].count(None) != 1:
        raise ValueError(
            "Must specify exactly two of "
            "top_padding, bottom_padding, target_height. "
            f"Received: top_padding={top_padding}, "
            f"bottom_padding={bottom_padding}, "
            f"target_height={target_height}"
        )
    if [left_padding, right_padding, target_width].count(None) != 1:
        raise ValueError(
            "Must specify exactly two of "
            "left_padding, right_padding, target_width. "
            f"Received: left_padding={left_padding}, "
            f"right_padding={right_padding}, "
            f"target_width={target_width}"
        )

    is_batch = False if len(images_shape) == 3 else True
    if data_format == "channels_last":
        height, width = images_shape[-3], images_shape[-2]
    else:
        height, width = images_shape[-2], images_shape[-1]

    # Infer padding
    if top_padding is None:
        top_padding = target_height - bottom_padding - height
    if bottom_padding is None:
        bottom_padding = target_height - top_padding - height
    if left_padding is None:
        left_padding = target_width - right_padding - width
    if right_padding is None:
        right_padding = target_width - left_padding - width

    if top_padding < 0:
        raise ValueError(
            f"top_padding must be >= 0. Received: top_padding={top_padding}"
        )
    if left_padding < 0:
        raise ValueError(
            f"left_padding must be >= 0. Received: left_padding={left_padding}"
        )
    if right_padding < 0:
        raise ValueError(
            "right_padding must be >= 0. "
            f"Received: right_padding={right_padding}"
        )
    if bottom_padding < 0:
        raise ValueError(
            "bottom_padding must be >= 0. "
            f"Received: bottom_padding={bottom_padding}"
        )

    # Compute pad_width
    pad_width = [[top_padding, bottom_padding], [left_padding, right_padding]]
    if data_format == "channels_last":
        pad_width = pad_width + [[0, 0]]
    else:
        pad_width = [[0, 0]] + pad_width
    if is_batch:
        pad_width = [[0, 0]] + pad_width

    padded_images = backend.numpy.pad(images, pad_width)
    return padded_images