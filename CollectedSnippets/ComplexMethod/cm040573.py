def gaussian_blur_np(
    images,
    kernel_size,
    sigma,
    data_format=None,
):
    def _create_gaussian_kernel(kernel_size, sigma, num_channels, dtype):
        def _get_gaussian_kernel1d(size, sigma):
            x = np.arange(size, dtype=dtype) - (size - 1) / 2
            kernel1d = np.exp(-0.5 * (x / sigma) ** 2)
            return kernel1d / np.sum(kernel1d)

        def _get_gaussian_kernel2d(size, sigma):
            kernel1d_x = _get_gaussian_kernel1d(size[0], sigma[0])
            kernel1d_y = _get_gaussian_kernel1d(size[1], sigma[1])
            return np.outer(kernel1d_y, kernel1d_x)

        kernel = _get_gaussian_kernel2d(kernel_size, sigma)
        kernel = kernel[:, :, np.newaxis]
        kernel = np.tile(kernel, (1, 1, num_channels))
        return kernel.astype(dtype)

    images = np.asarray(images)
    input_dtype = images.dtype
    kernel_size = np.asarray(kernel_size)

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

    num_channels = images.shape[-1]
    kernel = _create_gaussian_kernel(
        kernel_size, sigma, num_channels, input_dtype
    )
    batch_size, height, width, _ = images.shape

    kernel_h, kernel_w = kernel.shape[0], kernel.shape[1]
    pad_h = (kernel_h - 1) // 2
    pad_h_after = kernel_h - 1 - pad_h
    pad_w = (kernel_w - 1) // 2
    pad_w_after = kernel_w - 1 - pad_w

    padded_images = np.pad(
        images,
        (
            (0, 0),
            (pad_h, pad_h_after),
            (pad_w, pad_w_after),
            (0, 0),
        ),
        mode="constant",
    )

    blurred_images = np.zeros_like(images)
    kernel_reshaped = kernel.reshape((1, kernel_h, kernel_w, num_channels))

    for b in range(batch_size):
        image_patch = padded_images[b : b + 1, :, :, :]

    for i in range(height):
        for j in range(width):
            patch = image_patch[:, i : i + kernel_h, j : j + kernel_w, :]
            blurred_images[b, i, j, :] = np.sum(
                patch * kernel_reshaped, axis=(1, 2)
            )

    if data_format == "channels_first":
        blurred_images = np.transpose(blurred_images, (0, 3, 1, 2))
    if need_squeeze:
        blurred_images = np.squeeze(blurred_images, axis=0)

    return blurred_images