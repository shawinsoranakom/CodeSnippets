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
    """Resize images to size using the specified interpolation method.

    Args:
        images: Input image or batch of images. Must be 3D or 4D.
        size: Size of output image in `(height, width)` format.
        interpolation: Interpolation method. Available methods are `"nearest"`,
            `"bilinear"`, and `"bicubic"`. Defaults to `"bilinear"`.
        antialias: Whether to use an antialiasing filter when downsampling an
            image. Defaults to `False`.
        crop_to_aspect_ratio: If `True`, resize the images without aspect
            ratio distortion. When the original aspect ratio differs
            from the target aspect ratio, the output image will be
            cropped so as to return the
            largest possible window in the image (of size `(height, width)`)
            that matches the target aspect ratio. By default
            (`crop_to_aspect_ratio=False`), aspect ratio may not be preserved.
        pad_to_aspect_ratio: If `True`, pad the images without aspect
            ratio distortion. When the original aspect ratio differs
            from the target aspect ratio, the output image will be
            evenly padded on the short side.
        fill_mode: When using `pad_to_aspect_ratio=True`, padded areas
            are filled according to the given mode. Only `"constant"` is
            supported at this time
            (fill with constant value, equal to `fill_value`).
        fill_value: Float. Padding value to use when `pad_to_aspect_ratio=True`.
        data_format: A string specifying the data format of the input tensor.
            It can be either `"channels_last"` or `"channels_first"`.
            `"channels_last"` corresponds to inputs with shape
            `(batch, height, width, channels)`, while `"channels_first"`
            corresponds to inputs with shape `(batch, channels, height, width)`.
            If not specified, the value will default to
            `keras.config.image_data_format`.

    Returns:
        Resized image or batch of images.

    Examples:

    >>> x = np.random.random((2, 4, 4, 3)) # batch of 2 RGB images
    >>> y = keras.ops.image.resize(x, (2, 2))
    >>> y.shape
    (2, 2, 2, 3)

    >>> x = np.random.random((4, 4, 3)) # single RGB image
    >>> y = keras.ops.image.resize(x, (2, 2))
    >>> y.shape
    (2, 2, 3)

    >>> x = np.random.random((2, 3, 4, 4)) # batch of 2 RGB images
    >>> y = keras.ops.image.resize(x, (2, 2),
    ...     data_format="channels_first")
    >>> y.shape
    (2, 3, 2, 2)
    """
    if len(size) != 2:
        raise ValueError(
            "Expected `size` to be a tuple of 2 integers. "
            f"Received: size={size}"
        )
    if size[0] <= 0 or size[1] <= 0:
        raise ValueError(
            f"`size` must have positive height and width. Received: size={size}"
        )
    if len(images.shape) < 3 or len(images.shape) > 4:
        raise ValueError(
            "Invalid images rank: expected rank 3 (single image) "
            "or rank 4 (batch of images). Received input with shape: "
            f"images.shape={images.shape}"
        )
    if pad_to_aspect_ratio and crop_to_aspect_ratio:
        raise ValueError(
            "Only one of `pad_to_aspect_ratio` & `crop_to_aspect_ratio` "
            "can be `True`."
        )
    if any_symbolic_tensors((images,)):
        return Resize(
            size,
            interpolation=interpolation,
            antialias=antialias,
            data_format=data_format,
            crop_to_aspect_ratio=crop_to_aspect_ratio,
            pad_to_aspect_ratio=pad_to_aspect_ratio,
            fill_mode=fill_mode,
            fill_value=fill_value,
        ).symbolic_call(images)
    return _resize(
        images,
        size,
        interpolation=interpolation,
        antialias=antialias,
        crop_to_aspect_ratio=crop_to_aspect_ratio,
        data_format=data_format,
        pad_to_aspect_ratio=pad_to_aspect_ratio,
        fill_mode=fill_mode,
        fill_value=fill_value,
    )