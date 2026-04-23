def _load_image_grain(
    path,
    image_size,
    num_channels,
    interpolation,
    data_format,
    crop_to_aspect_ratio=False,
    pad_to_aspect_ratio=False,
):
    """Load an image from a path and resize it."""
    from keras.src import backend
    from keras.src import ops

    if pil_image is None:
        raise ImportError(
            "Could not import PIL.Image. The use of `load_img` requires PIL."
        )
    if pad_to_aspect_ratio and crop_to_aspect_ratio:
        raise ValueError(
            "Only one of `pad_to_aspect_ratio`, `crop_to_aspect_ratio`"
            " can be set to `True`."
        )

    if isinstance(path, io.BytesIO):
        img = pil_image.open(path)
    elif isinstance(path, (pathlib.Path, bytes, str)):
        if isinstance(path, pathlib.Path):
            path = str(path.resolve())
        img = pil_image.open(path)
    else:
        raise TypeError(
            f"path should be path-like or io.BytesIO, not {type(path)}"
        )
    if num_channels == 1:
        # if image is not already an 8-bit, 16-bit or 32-bit grayscale image
        # convert it to an 8-bit grayscale image.
        if img.mode not in ("L", "I;16", "I"):
            img = img.convert("L")
    elif num_channels == 4:
        if img.mode != "RGBA":
            img = img.convert("RGBA")
    elif num_channels == 3:
        if img.mode != "RGB":
            img = img.convert("RGB")
    else:
        raise ValueError(
            "num_channels must be 1, 3 or 4. "
            f"Received: num_channels={num_channels}"
        )

    with backend.device_scope("cpu"):
        img = ops.convert_to_tensor(np.array(img), dtype="float32")
        if len(img.shape) == 2:
            # If the image is grayscale, expand dims to add channel axis.
            # The reason is that `ops.image.resize` expects 3D or 4D tensors.
            img = ops.expand_dims(img, axis=-1)
        if data_format == "channels_first":
            img = ops.transpose(img, (2, 0, 1))
        img = ops.image.resize(
            img,
            size=image_size,
            interpolation=interpolation,
            crop_to_aspect_ratio=crop_to_aspect_ratio,
            pad_to_aspect_ratio=pad_to_aspect_ratio,
            data_format=data_format,
        )
        if backend.backend() == "tensorflow":
            if data_format == "channels_last":
                img.set_shape((image_size[0], image_size[1], num_channels))
            else:
                img.set_shape((num_channels, image_size[0], image_size[1]))
    return img