def _extract_patches_3d(
    volumes,
    size,
    strides=None,
    dilation_rate=1,
    padding="valid",
    data_format=None,
):
    if isinstance(size, int):
        patch_d = patch_h = patch_w = size
    elif len(size) == 3:
        patch_d, patch_h, patch_w = size
    else:
        raise TypeError(
            "Invalid `size` argument. Expected an "
            f"int or a tuple of length 3. Received: size={size}"
        )
    if strides is None:
        strides = size
    if isinstance(strides, int):
        strides = (strides, strides, strides)
    if len(strides) != 3:
        raise ValueError(f"Invalid `strides` argument. Got: {strides}")
    data_format = backend.standardize_data_format(data_format)
    if data_format == "channels_last":
        channels_in = volumes.shape[-1]
    elif data_format == "channels_first":
        channels_in = volumes.shape[-4]
    out_dim = patch_d * patch_w * patch_h * channels_in
    kernel = backend.numpy.eye(out_dim, dtype=volumes.dtype)
    kernel = backend.numpy.reshape(
        kernel, (patch_d, patch_h, patch_w, channels_in, out_dim)
    )
    _unbatched = False
    if len(volumes.shape) == 4:
        _unbatched = True
        volumes = backend.numpy.expand_dims(volumes, axis=0)
    patches = backend.nn.conv(
        inputs=volumes,
        kernel=kernel,
        strides=strides,
        padding=padding,
        data_format=data_format,
        dilation_rate=dilation_rate,
    )
    if _unbatched:
        patches = backend.numpy.squeeze(patches, axis=0)
    return patches