def perspective_transform(
    images,
    start_points,
    end_points,
    interpolation="bilinear",
    fill_value=0,
    data_format=None,
):
    data_format = backend.standardize_data_format(data_format)

    images = convert_to_tensor(images)
    dtype = backend.standardize_dtype(images.dtype)
    start_points = convert_to_tensor(start_points, dtype=dtype)
    end_points = convert_to_tensor(end_points, dtype=dtype)

    if interpolation not in AFFINE_TRANSFORM_INTERPOLATIONS.keys():
        raise ValueError(
            "Invalid value for argument `interpolation`. Expected of one "
            f"{set(AFFINE_TRANSFORM_INTERPOLATIONS.keys())}. Received: "
            f"interpolation={interpolation}"
        )

    if images.ndim not in (3, 4):
        raise ValueError(
            "Invalid images rank: expected rank 3 (single image) "
            "or rank 4 (batch of images). Received input with shape: "
            f"images.shape={images.shape}"
        )

    if start_points.shape[-2:] != (4, 2) or start_points.dim() not in (2, 3):
        raise ValueError(
            "Invalid start_points shape: expected (4,2) for a single image"
            f" or (N,4,2) for a batch. Received shape: {start_points.shape}"
        )
    if end_points.shape[-2:] != (4, 2) or end_points.dim() not in (2, 3):
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
    if images.ndim == 3:
        images = images.unsqueeze(dim=0)
        need_squeeze = True

    if start_points.ndim == 2:
        start_points = start_points.unsqueeze(dim=0)
    if end_points.ndim == 2:
        end_points = end_points.unsqueeze(dim=0)

    if data_format == "channels_first":
        images = images.permute((0, 2, 3, 1))

    batch_size, height, width, channels = images.shape

    transforms = compute_homography_matrix(start_points, end_points)

    if transforms.dim() == 1:
        transforms = transforms.unsqueeze(0)
    if transforms.shape[0] == 1 and batch_size > 1:
        transforms = transforms.repeat(batch_size, 1)

    grid_x, grid_y = torch.meshgrid(
        torch.arange(width, dtype=to_torch_dtype(dtype), device=images.device),
        torch.arange(height, dtype=to_torch_dtype(dtype), device=images.device),
        indexing="xy",
    )

    output = torch.empty(
        [batch_size, height, width, channels],
        dtype=to_torch_dtype(dtype),
        device=images.device,
    )

    for i in range(batch_size):
        a0, a1, a2, a3, a4, a5, a6, a7 = transforms[i]
        denom = a6 * grid_x + a7 * grid_y + 1.0
        x_in = (a0 * grid_x + a1 * grid_y + a2) / denom
        y_in = (a3 * grid_x + a4 * grid_y + a5) / denom

        coords = torch.stack([y_in.flatten(), x_in.flatten()], dim=0)
        mapped_channels = []
        for channel in range(channels):
            channel_img = images[i, :, :, channel]
            mapped_channel = map_coordinates(
                channel_img,
                coords,
                order=AFFINE_TRANSFORM_INTERPOLATIONS[interpolation],
                fill_mode="constant",
                fill_value=fill_value,
            )
            mapped_channels.append(mapped_channel.reshape(height, width))
        output[i] = torch.stack(mapped_channels, dim=-1)

    if data_format == "channels_first":
        output = output.permute((0, 3, 1, 2))
    if need_squeeze:
        output = output.squeeze(dim=0)

    return output