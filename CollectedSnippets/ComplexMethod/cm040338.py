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
    if images.ndim == 3:
        images = images.unsqueeze(dim=0)
        need_squeeze = True

    if data_format == "channels_last":
        batch_size, height, width, channels = images.shape
        channel_axis = -1
    else:
        batch_size, channels, height, width = images.shape
        channel_axis = 1

    generator = _torch_seed_generator(seed) if get_device() == "meta" else None
    dx = (
        torch.normal(
            0.0,
            1.0,
            size=(batch_size, height, width),
            generator=generator,
            dtype=input_dtype,
            device=images.device,
        )
        * sigma
    )

    dy = (
        torch.normal(
            0.0,
            1.0,
            size=(batch_size, height, width),
            generator=generator,
            dtype=input_dtype,
            device=images.device,
        )
        * sigma
    )

    dx = gaussian_blur(
        dx.unsqueeze(dim=channel_axis),
        kernel_size=kernel_size,
        sigma=(sigma, sigma),
        data_format=data_format,
    )
    dy = gaussian_blur(
        dy.unsqueeze(dim=channel_axis),
        kernel_size=kernel_size,
        sigma=(sigma, sigma),
        data_format=data_format,
    )

    dx = dx.squeeze()
    dy = dy.squeeze()

    x, y = torch.meshgrid(
        torch.arange(width), torch.arange(height), indexing="xy"
    )
    x, y = x.unsqueeze(0).to(images.device), y.unsqueeze(0).to(images.device)

    distorted_x = x + alpha * dx
    distorted_y = y + alpha * dy

    transformed_images = torch.zeros_like(images)

    if data_format == "channels_last":
        for i in range(channels):
            transformed_images[..., i] = torch.stack(
                [
                    map_coordinates(
                        images[b, ..., i],
                        [distorted_y[b], distorted_x[b]],
                        order=AFFINE_TRANSFORM_INTERPOLATIONS[interpolation],
                        fill_mode=fill_mode,
                        fill_value=fill_value,
                    )
                    for b in range(batch_size)
                ]
            )
    else:
        for i in range(channels):
            transformed_images[:, i, :, :] = torch.stack(
                [
                    map_coordinates(
                        images[b, i, ...],
                        [distorted_y[b], distorted_x[b]],
                        order=AFFINE_TRANSFORM_INTERPOLATIONS[interpolation],
                        fill_mode=fill_mode,
                        fill_value=fill_value,
                    )
                    for b in range(batch_size)
                ]
            )

    if need_squeeze:
        transformed_images = transformed_images.squeeze(0)
    transformed_images = transformed_images.to(input_dtype)

    return transformed_images