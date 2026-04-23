def infer_channel_dimension_format(
    image: np.ndarray, num_channels: int | tuple[int, ...] | None = None
) -> ChannelDimension:
    """
    Infers the channel dimension format of `image`.

    Args:
        image (`np.ndarray`):
            The image to infer the channel dimension of.
        num_channels (`int` or `tuple[int, ...]`, *optional*, defaults to `(1, 3)`):
            The number of channels of the image.

    Returns:
        The channel dimension of the image.
    """
    num_channels = num_channels if num_channels is not None else (1, 3)
    num_channels = (num_channels,) if isinstance(num_channels, int) else num_channels

    if image.ndim == 3:
        first_dim, last_dim = 0, 2
    elif image.ndim == 4:
        first_dim, last_dim = 1, 3
    elif image.ndim == 5:
        first_dim, last_dim = 2, 4
    else:
        raise ValueError(f"Unsupported number of image dimensions: {image.ndim}")

    if image.shape[first_dim] in num_channels and image.shape[last_dim] in num_channels:
        logger.warning(
            f"The channel dimension is ambiguous. Got image shape {image.shape}. Assuming channels are the first dimension. Use the [input_data_format](https://huggingface.co/docs/transformers/main/internal/image_processing_utils#transformers.image_transforms.rescale.input_data_format) parameter to assign the channel dimension."
        )
        return ChannelDimension.FIRST
    elif image.shape[first_dim] in num_channels:
        return ChannelDimension.FIRST
    elif image.shape[last_dim] in num_channels:
        return ChannelDimension.LAST
    raise ValueError("Unable to infer channel dimension format")