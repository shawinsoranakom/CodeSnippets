def gaussian_blur(
    images, kernel_size=(3, 3), sigma=(1.0, 1.0), data_format=None
):
    def _create_gaussian_kernel(kernel_size, sigma):
        # Always build the kernel in f32 for numerical stability and
        # compatibility (bfloat16 / f16 are not fully supported by all ops).
        def _get_gaussian_kernel1d(size, sigma):
            x = ov_opset.subtract(
                ov_opset.range(0, size, 1, output_type=Type.f32).output(0),
                ov_opset.constant((size - 1) / 2.0, Type.f32).output(0),
            ).output(0)

            sigma_const = ov_opset.constant(float(sigma), Type.f32).output(0)
            exponent = ov_opset.divide(x, sigma_const).output(0)
            exponent = ov_opset.multiply(exponent, exponent).output(0)
            exponent = ov_opset.multiply(
                exponent, ov_opset.constant(-0.5, Type.f32).output(0)
            ).output(0)
            kernel1d = ov_opset.exp(exponent).output(0)
            kernel1d_sum = ov_opset.reduce_sum(
                kernel1d, reduction_axes=0, keep_dims=False
            ).output(0)

            return ov_opset.divide(kernel1d, kernel1d_sum).output(0)

        def _get_gaussian_kernel2d(size, sigma):
            kernel1d_x = _get_gaussian_kernel1d(size[0], sigma[0])
            kernel1d_y = _get_gaussian_kernel1d(size[1], sigma[1])

            # kernel1d_x has kH elements -> row vector [1, kH]
            kernel1d_x = ov_opset.reshape(
                kernel1d_x,
                ov_opset.constant([1, int(size[0])], Type.i32).output(0),
                False,
            ).output(0)

            # kernel1d_y has kW elements -> column vector [kW, 1]
            kernel1d_y = ov_opset.reshape(
                kernel1d_y,
                ov_opset.constant([int(size[1]), 1], Type.i32).output(0),
                False,
            ).output(0)
            return ov_opset.multiply(kernel1d_y, kernel1d_x).output(0)

        return _get_gaussian_kernel2d(kernel_size, sigma)

    data_format = backend.standardize_data_format(data_format)
    images = convert_to_tensor(images)
    input_shape = images.shape
    ov_type = get_ov_output(images).get_element_type()

    if len(input_shape) not in (3, 4):
        raise ValueError(
            "Invalid images rank: expected rank 3 (single image) "
            "or rank 4 (batch of images). Received input with shape: "
            f"images.shape={input_shape}"
        )

    # bfloat16 is not supported by all OV ops used here; promote to f32.
    # f16 constants in range() would mismatch with the f32 arithmetic
    # constants in the kernel builder, so promote f16 to f32 as well.
    compute_type = Type.f32 if ov_type in (Type.bf16, Type.f16) else ov_type
    images = get_ov_output(images)
    if compute_type != ov_type:
        images = ov_opset.convert(images, compute_type).output(0)

    need_squeeze = False
    if len(input_shape) == 3:
        images = ov_opset.unsqueeze(images, axes=[0]).output(0)
        need_squeeze = True

    if data_format == "channels_last":
        images = ov_opset.transpose(
            images,
            ov_opset.constant([0, 3, 1, 2], Type.i32).output(0),
        ).output(0)

    num_channels = ov_opset.gather(
        ov_opset.shape_of(images, Type.i32).output(0),
        ov_opset.constant([1], Type.i32).output(0),
        ov_opset.constant(0, Type.i32).output(0),
    ).output(0)
    # Kernel is always built in f32; convert to compute_type before conv.
    kernel = _create_gaussian_kernel(kernel_size, sigma)
    kernel = ov_opset.convert(kernel, compute_type).output(0)

    kernel = ov_opset.reshape(
        kernel,
        ov_opset.constant(
            [1, 1, kernel_size[0], kernel_size[1]], Type.i32
        ).output(0),
        False,
    ).output(0)

    target_shape = ov_opset.concat(
        [
            num_channels,
            ov_opset.constant(
                [1, 1, kernel_size[0], kernel_size[1]], Type.i32
            ).output(0),
        ],
        axis=0,
    ).output(0)

    kernel = ov_opset.broadcast(kernel, target_shape).output(0)

    blurred_images = ov_opset.group_convolution(
        images,
        kernel,
        [1, 1],
        [(kernel_size[0] - 1) // 2, (kernel_size[1] - 1) // 2],
        [
            kernel_size[0] - 1 - (kernel_size[0] - 1) // 2,
            kernel_size[1] - 1 - (kernel_size[1] - 1) // 2,
        ],
        [1, 1],
    ).output(0)

    # Cast back to the original dtype if we promoted for computation.
    if compute_type != ov_type:
        blurred_images = ov_opset.convert(blurred_images, ov_type).output(0)

    if data_format == "channels_last":
        blurred_images = ov_opset.transpose(
            blurred_images,
            ov_opset.constant([0, 2, 3, 1], Type.i32).output(0),
        ).output(0)

    if need_squeeze:
        blurred_images = ov_opset.squeeze(blurred_images, axes=[0]).output(0)

    return OpenVINOKerasTensor(blurred_images)