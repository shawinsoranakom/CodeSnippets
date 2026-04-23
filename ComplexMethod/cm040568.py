def _crop_images(
    images,
    top_cropping,
    left_cropping,
    bottom_cropping,
    right_cropping,
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
    if [top_cropping, bottom_cropping, target_height].count(None) != 1:
        raise ValueError(
            "Must specify exactly two of "
            "top_cropping, bottom_cropping, target_height. "
            f"Received: top_cropping={top_cropping}, "
            f"bottom_cropping={bottom_cropping}, "
            f"target_height={target_height}"
        )
    if [left_cropping, right_cropping, target_width].count(None) != 1:
        raise ValueError(
            "Must specify exactly two of "
            "left_cropping, right_cropping, target_width. "
            f"Received: left_cropping={left_cropping}, "
            f"right_cropping={right_cropping}, "
            f"target_width={target_width}"
        )

    is_batch = False if len(images_shape) == 3 else True
    if data_format == "channels_last":
        height, width = images_shape[-3], images_shape[-2]
        channels = images_shape[-1]
    else:
        height, width = images_shape[-2], images_shape[-1]
        channels = images_shape[-3]

    # Infer padding
    if top_cropping is None:
        top_cropping = height - target_height - bottom_cropping
    if target_height is None:
        target_height = height - bottom_cropping - top_cropping
    if left_cropping is None:
        left_cropping = width - target_width - right_cropping
    if target_width is None:
        target_width = width - right_cropping - left_cropping

    if top_cropping < 0:
        raise ValueError(
            f"top_cropping must be >= 0. Received: top_cropping={top_cropping}"
        )
    if target_height < 0:
        raise ValueError(
            "target_height must be >= 0. "
            f"Received: target_height={target_height}"
        )
    if left_cropping < 0:
        raise ValueError(
            "left_cropping must be >= 0. "
            f"Received: left_cropping={left_cropping}"
        )
    if target_width < 0:
        raise ValueError(
            f"target_width must be >= 0. Received: target_width={target_width}"
        )

    # Compute start_indices and shape
    start_indices = [top_cropping, left_cropping]
    shape = [target_height, target_width]
    if data_format == "channels_last":
        start_indices = start_indices + [0]
        shape = shape + [channels]
    else:
        start_indices = [0] + start_indices
        shape = [channels] + shape
    if is_batch:
        batch_size = images_shape[0]
        start_indices = [0] + start_indices
        shape = [batch_size] + shape

    cropped_images = ops.slice(images, start_indices, shape)
    return cropped_images