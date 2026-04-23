def gaussian_blur(
    images, kernel_size=(3, 3), sigma=(1.0, 1.0), data_format=None
):
    def _create_gaussian_kernel(kernel_size, sigma, num_channels, dtype):
        def _get_gaussian_kernel1d(size, sigma):
            x = np.arange(size, dtype=dtype) - (size - 1) / 2
            kernel1d = np.exp(-0.5 * (x / sigma) ** 2)
            return kernel1d / np.sum(kernel1d)

        def _get_gaussian_kernel2d(size, sigma):
            size = np.asarray(size, dtype)
            kernel1d_x = _get_gaussian_kernel1d(size[0], sigma[0])
            kernel1d_y = _get_gaussian_kernel1d(size[1], sigma[1])
            return np.outer(kernel1d_y, kernel1d_x)

        kernel = _get_gaussian_kernel2d(kernel_size, sigma)
        kernel = kernel[:, :, np.newaxis]
        kernel = np.tile(kernel, (1, 1, num_channels))
        return kernel.astype(dtype)

    images = convert_to_tensor(images)
    kernel_size = convert_to_tensor(kernel_size)
    sigma = convert_to_tensor(sigma)
    input_dtype = backend.standardize_dtype(images.dtype)
    # `scipy.signal.convolve2d` lacks support for float16 and bfloat16.
    compute_dtype = backend.result_type(input_dtype, "float32")
    images = images.astype(compute_dtype)
    sigma = sigma.astype(compute_dtype)

    if len(images.shape) not in (3, 4):
        raise ValueError(
            "Invalid images rank: expected rank 3 (single image) "
            "or rank 4 (batch of images). Received input with shape: "
            f"images.shape={images.shape}"
        )

    need_squeeze = False
    if len(images.shape) == 3:
        images = np.expand_dims(images, axis=0)
        need_squeeze = True

    if data_format == "channels_first":
        images = np.transpose(images, (0, 2, 3, 1))

    batch_size, height, width, num_channels = images.shape

    kernel = _create_gaussian_kernel(
        kernel_size, sigma, num_channels, input_dtype
    )

    kernel_h, kernel_w = kernel.shape[0], kernel.shape[1]
    pad_h = (kernel_h - 1) // 2
    pad_h_after = kernel_h - 1 - pad_h
    pad_w = (kernel_w - 1) // 2
    pad_w_after = kernel_w - 1 - pad_w

    blurred_images = np.empty_like(images)

    for b in range(batch_size):
        for ch in range(num_channels):
            padded = np.pad(
                images[b, :, :, ch],
                ((pad_h, pad_h_after), (pad_w, pad_w_after)),
                mode="constant",
            )
            blurred_images[b, :, :, ch] = scipy.signal.convolve2d(
                padded, kernel[:, :, ch], mode="valid"
            )

    if data_format == "channels_first":
        blurred_images = np.transpose(blurred_images, (0, 3, 1, 2))
    if need_squeeze:
        blurred_images = np.squeeze(blurred_images, axis=0)
    return blurred_images.astype(input_dtype)