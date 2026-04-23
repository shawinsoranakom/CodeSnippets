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
    if interpolation in UNSUPPORTED_INTERPOLATIONS:
        raise ValueError(
            "Resizing with Lanczos interpolation is "
            "not supported by the PyTorch backend. "
            f"Received: interpolation={interpolation}."
        )
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
    images = convert_to_tensor(images)
    if images.ndim not in (3, 4):
        raise ValueError(
            "Invalid images rank: expected rank 3 (single image) "
            "or rank 4 (batch of images). Received input with shape: "
            f"images.shape={images.shape}"
        )
    images, need_cast, need_squeeze, out_dtype = _cast_squeeze_in(
        images, [torch.float32, torch.float64]
    )
    if data_format == "channels_last":
        images = images.permute((0, 3, 1, 2))

    if crop_to_aspect_ratio:
        shape = images.shape
        height, width = shape[-2], shape[-1]
        target_height, target_width = size
        crop_height = int(float(width * target_height) / target_width)
        crop_height = max(min(height, crop_height), 1)
        crop_width = int(float(height * target_width) / target_height)
        crop_width = max(min(width, crop_width), 1)
        crop_box_hstart = int(float(height - crop_height) / 2)
        crop_box_wstart = int(float(width - crop_width) / 2)
        images = images[
            :,
            :,
            crop_box_hstart : crop_box_hstart + crop_height,
            crop_box_wstart : crop_box_wstart + crop_width,
        ]
    elif pad_to_aspect_ratio:
        shape = images.shape
        height, width = shape[-2], shape[-1]
        target_height, target_width = size
        pad_height = int(float(width * target_height) / target_width)
        pad_height = max(height, pad_height)
        pad_width = int(float(height * target_width) / target_height)
        pad_width = max(width, pad_width)
        img_box_hstart = int(float(pad_height - height) / 2)
        img_box_wstart = int(float(pad_width - width) / 2)

        batch_size = images.shape[0]
        channels = images.shape[1]
        if img_box_hstart > 0:
            padded_img = torch.cat(
                [
                    torch.ones(
                        (batch_size, channels, img_box_hstart, width),
                        dtype=images.dtype,
                        device=images.device,
                    )
                    * fill_value,
                    images,
                    torch.ones(
                        (batch_size, channels, img_box_hstart, width),
                        dtype=images.dtype,
                        device=images.device,
                    )
                    * fill_value,
                ],
                axis=2,
            )
        else:
            padded_img = images
        if img_box_wstart > 0:
            padded_img = torch.cat(
                [
                    torch.ones(
                        (batch_size, channels, height, img_box_wstart),
                        dtype=images.dtype,
                        device=images.device,
                    ),
                    padded_img,
                    torch.ones(
                        (batch_size, channels, height, img_box_wstart),
                        dtype=images.dtype,
                        device=images.device,
                    )
                    * fill_value,
                ],
                axis=3,
            )
        images = padded_img

    # This implementation is based on
    # https://github.com/pytorch/vision/blob/main/torchvision/transforms/_functional_tensor.py
    if antialias and interpolation not in ("bilinear", "bicubic"):
        # We manually set it to False to avoid an error downstream in
        # interpolate(). This behaviour is documented: the parameter is
        # irrelevant for modes that are not bilinear or bicubic. We used to
        # raise an error here, but now we don't use True as the default.
        antialias = False
    # Define align_corners to avoid warnings
    align_corners = False if interpolation in ("bilinear", "bicubic") else None
    resized = F.interpolate(
        images,
        size=size,
        mode=RESIZE_INTERPOLATIONS[interpolation],
        align_corners=align_corners,
        antialias=antialias,
    )
    if interpolation == "bicubic" and out_dtype == torch.uint8:
        resized = resized.clamp(min=0, max=255)
    if data_format == "channels_last":
        resized = resized.permute((0, 2, 3, 1))
    resized = _cast_squeeze_out(
        resized,
        need_cast=need_cast,
        need_squeeze=need_squeeze,
        out_dtype=out_dtype,
    )
    return resized