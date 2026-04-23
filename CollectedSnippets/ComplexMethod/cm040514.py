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
    if interpolation not in AFFINE_TRANSFORM_INTERPOLATIONS:
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
    images_ov = get_ov_output(images)
    ov_type = images_ov.get_element_type()
    compute_type = Type.f32

    need_squeeze = False
    if len(images.shape) == 3:
        images_ov = ov_opset.unsqueeze(images_ov, axes=[0]).output(0)
        need_squeeze = True

    if data_format == "channels_last":
        images_ov_cf = ov_opset.transpose(
            images_ov,
            ov_opset.constant([0, 3, 1, 2], Type.i32).output(0),
        ).output(0)
    else:
        images_ov_cf = images_ov

    images_ov_cf = ov_opset.convert(images_ov_cf, compute_type).output(0)

    shape_node = ov_opset.shape_of(images_ov_cf, output_type=Type.i32).output(0)
    axis0 = ov_opset.constant(0, Type.i32).output(0)

    def dim(i):
        return ov_opset.gather(
            shape_node, ov_opset.constant(i, Type.i32).output(0), axis0
        ).output(0)

    B = dim(0)
    C = dim(1)
    H = dim(2)
    W = dim(3)

    sigma_val = float(sigma)
    alpha_val = float(alpha)
    kernel_size_1d = int(6 * sigma_val) | 1

    # OV random ops require static seed attributes, so symbolic seeds must be
    # materialized via convert_to_numpy. This is an unavoidable sync point given
    # the OV backend's stateless random design.
    seed_val = draw_seed(seed)
    if isinstance(seed_val, OpenVINOKerasTensor):
        s = convert_to_numpy(seed_val)
    else:
        s = seed_val.data
    seed1 = max(1, int(s[0]) & 0x7FFFFFFF)
    seed2 = max(1, int(s[1]) & 0x7FFFFFFF) if len(s) > 1 else 1

    def to_1d(scalar):
        return ov_opset.reshape(
            scalar, ov_opset.constant([1], Type.i32).output(0), False
        ).output(0)

    bhw_shape = ov_opset.concat(
        [to_1d(B), to_1d(H), to_1d(W)],
        axis=0,
    ).output(0)

    dx = _random_normal(bhw_shape, Type.f32, seed1, seed2)  # [B, H, W]
    dy = _random_normal(bhw_shape, Type.f32, seed1 + 1, seed2)  # [B, H, W]

    # Scale by sigma before gaussian blur
    sigma_const = ov_opset.constant(sigma_val, Type.f32).output(0)
    dx = ov_opset.multiply(dx, sigma_const).output(0)
    dy = ov_opset.multiply(dy, sigma_const).output(0)

    # Apply gaussian blur to smooth the displacement fields
    # Add channel dim: [B, 1, H, W] for channels_first gaussian_blur
    dx_4d = ov_opset.unsqueeze(dx, axes=[1]).output(0)
    dy_4d = ov_opset.unsqueeze(dy, axes=[1]).output(0)

    dx_blurred = gaussian_blur(
        OpenVINOKerasTensor(dx_4d),
        kernel_size=(kernel_size_1d, kernel_size_1d),
        sigma=(sigma_val, sigma_val),
        data_format="channels_first",
    )
    dy_blurred = gaussian_blur(
        OpenVINOKerasTensor(dy_4d),
        kernel_size=(kernel_size_1d, kernel_size_1d),
        sigma=(sigma_val, sigma_val),
        data_format="channels_first",
    )
    dx_blurred = ov_opset.squeeze(get_ov_output(dx_blurred), axes=[1]).output(
        0
    )  # [B, H, W]
    dy_blurred = ov_opset.squeeze(get_ov_output(dy_blurred), axes=[1]).output(
        0
    )  # [B, H, W]

    H_f = ov_opset.convert(H, Type.f32).output(0)
    W_f = ov_opset.convert(W, Type.f32).output(0)
    zero_f = ov_opset.constant(0.0, Type.f32).output(0)
    one_f = ov_opset.constant(1.0, Type.f32).output(0)
    r_h = ov_opset.range(zero_f, H_f, one_f, output_type=Type.f32).output(0)
    r_w = ov_opset.range(zero_f, W_f, one_f, output_type=Type.f32).output(0)
    hw_shape = ov_opset.concat([to_1d(H), to_1d(W)], axis=0).output(0)

    y_base = ov_opset.broadcast(
        ov_opset.reshape(
            r_h,
            ov_opset.concat(
                [to_1d(H), ov_opset.constant([1], Type.i32).output(0)], axis=0
            ).output(0),
            False,
        ).output(0),
        hw_shape,
    ).output(0)  # [H, W]
    x_base = ov_opset.broadcast(
        ov_opset.reshape(
            r_w,
            ov_opset.concat(
                [ov_opset.constant([1], Type.i32).output(0), to_1d(W)], axis=0
            ).output(0),
            False,
        ).output(0),
        hw_shape,
    ).output(0)  # [H, W]

    bhw_bcast = ov_opset.concat([to_1d(B), to_1d(H), to_1d(W)], axis=0).output(
        0
    )
    y_base_b = ov_opset.broadcast(
        ov_opset.unsqueeze(y_base, axes=[0]).output(0), bhw_bcast
    ).output(0)
    x_base_b = ov_opset.broadcast(
        ov_opset.unsqueeze(x_base, axes=[0]).output(0), bhw_bcast
    ).output(0)

    alpha_const = ov_opset.constant(alpha_val, Type.f32).output(0)
    distorted_x = ov_opset.add(
        x_base_b, ov_opset.multiply(alpha_const, dx_blurred).output(0)
    ).output(0)
    distorted_y = ov_opset.add(
        y_base_b, ov_opset.multiply(alpha_const, dy_blurred).output(0)
    ).output(0)

    # Build coords [3, B, H, W, C] — (row=y, col=x, chan) per output pixel
    C_f = ov_opset.convert(C, Type.f32).output(0)
    r_c = ov_opset.range(zero_f, C_f, one_f, output_type=Type.f32).output(0)

    bhwc_shape = ov_opset.concat(
        [to_1d(B), to_1d(H), to_1d(W), to_1d(C)], axis=0
    ).output(0)

    y_bhwc = ov_opset.broadcast(
        ov_opset.unsqueeze(distorted_y, axes=[3]).output(0), bhwc_shape
    ).output(0)
    x_bhwc = ov_opset.broadcast(
        ov_opset.unsqueeze(distorted_x, axes=[3]).output(0), bhwc_shape
    ).output(0)
    chan_bhwc = ov_opset.broadcast(
        ov_opset.reshape(
            r_c,
            ov_opset.concat(
                [ov_opset.constant([1, 1, 1], Type.i32).output(0), to_1d(C)],
                axis=0,
            ).output(0),
            False,
        ).output(0),
        bhwc_shape,
    ).output(0)

    B_f = ov_opset.convert(B, Type.f32).output(0)
    r_b = ov_opset.range(zero_f, B_f, one_f, output_type=Type.f32).output(0)
    batch_bhwc = ov_opset.broadcast(
        ov_opset.reshape(
            r_b,
            ov_opset.concat(
                [to_1d(B), ov_opset.constant([1, 1, 1], Type.i32).output(0)],
                axis=0,
            ).output(0),
            False,
        ).output(0),
        bhwc_shape,
    ).output(0)

    # coords: [4, B, H, W, C] — (batch, row=y, col=x, chan)
    coords = ov_opset.concat(
        [
            ov_opset.unsqueeze(batch_bhwc, axes=[0]).output(0),
            ov_opset.unsqueeze(y_bhwc, axes=[0]).output(0),
            ov_opset.unsqueeze(x_bhwc, axes=[0]).output(0),
            ov_opset.unsqueeze(chan_bhwc, axes=[0]).output(0),
        ],
        axis=0,
    ).output(0)  # [4, B, H, W, C]

    # images_ov_cf is [B, C, H, W] but map_coordinates needs [B, H, W, C]
    images_bhwc = ov_opset.transpose(
        images_ov_cf,
        ov_opset.constant([0, 2, 3, 1], Type.i32).output(0),
    ).output(0)

    result = map_coordinates(
        OpenVINOKerasTensor(images_bhwc),
        OpenVINOKerasTensor(coords),
        order=AFFINE_TRANSFORM_INTERPOLATIONS[interpolation],
        fill_mode=fill_mode,
        fill_value=fill_value,
    )
    result = get_ov_output(result)

    if ov_type.is_integral():
        result = ov_opset.round(result, mode="half_to_even").output(0)
    result = ov_opset.convert(result, ov_type).output(0)

    if data_format == "channels_first":
        result = ov_opset.transpose(
            result,
            ov_opset.constant([0, 3, 1, 2], Type.i32).output(0),
        ).output(0)
    if need_squeeze:
        result = ov_opset.squeeze(result, axes=[0]).output(0)

    return OpenVINOKerasTensor(result)