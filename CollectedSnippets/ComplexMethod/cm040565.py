def _extract_patches_2d(
    images,
    size,
    strides=None,
    dilation_rate=1,
    padding="valid",
    data_format=None,
):
    if isinstance(size, int):
        patch_h = patch_w = size
    elif len(size) == 2:
        patch_h, patch_w = size[0], size[1]
    else:
        raise TypeError(
            "Invalid `size` argument. Expected an "
            f"int or a tuple of length 2. Received: size={size}"
        )
    data_format = backend.standardize_data_format(data_format)
    if data_format == "channels_last":
        channels_in = images.shape[-1]
    elif data_format == "channels_first":
        channels_in = images.shape[-3]
    if not strides:
        strides = size
    out_dim = patch_h * patch_w * channels_in
    kernel = backend.numpy.eye(out_dim, dtype=images.dtype)
    kernel = backend.numpy.reshape(
        kernel, (patch_h, patch_w, channels_in, out_dim)
    )
    _unbatched = False
    if len(images.shape) == 3:
        _unbatched = True
        images = backend.numpy.expand_dims(images, axis=0)
    patches = backend.nn.conv(
        inputs=images,
        kernel=kernel,
        strides=strides,
        padding=padding,
        data_format=data_format,
        dilation_rate=dilation_rate,
    )
    if _unbatched:
        patches = backend.numpy.squeeze(patches, axis=0)
    return patches