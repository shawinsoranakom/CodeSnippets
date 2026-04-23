def perspective_transform(
    images,
    start_points,
    end_points,
    interpolation="bilinear",
    fill_value=0,
    data_format=None,
):
    data_format = backend.standardize_data_format(data_format)
    if interpolation not in AFFINE_TRANSFORM_INTERPOLATIONS:
        raise ValueError(
            "Invalid value for argument `interpolation`. Expected of one "
            f"{set(AFFINE_TRANSFORM_INTERPOLATIONS.keys())}. Received: "
            f"interpolation={interpolation}"
        )

    images = convert_to_tensor(images)
    start_points = convert_to_tensor(start_points)
    end_points = convert_to_tensor(end_points)
    images_ov = get_ov_output(images)
    sp_ov = get_ov_output(start_points)
    ep_ov = get_ov_output(end_points)

    if len(images.shape) not in (3, 4):
        raise ValueError(
            "Invalid images rank: expected rank 3 (single image) "
            "or rank 4 (batch of images). Received input with shape: "
            f"images.shape={images.shape}"
        )
    if len(start_points.shape) not in (2, 3) or tuple(start_points.shape)[
        -2:
    ] != (4, 2):
        raise ValueError(
            "Invalid start_points shape: expected (4,2) for a single image"
            f" or (N,4,2) for a batch. Received shape: {start_points.shape}"
        )
    if len(end_points.shape) not in (2, 3) or tuple(end_points.shape)[-2:] != (
        4,
        2,
    ):
        raise ValueError(
            "Invalid end_points shape: expected (4,2) for a single image"
            f" or (N,4,2) for a batch. Received shape: {end_points.shape}"
        )

    ov_type = images_ov.get_element_type()
    compute_type = Type.f32

    need_squeeze = False
    if len(images.shape) == 3:
        images_ov = ov_opset.unsqueeze(images_ov, axes=[0]).output(0)
        need_squeeze = True
    if len(start_points.shape) == 2:
        sp_ov = ov_opset.unsqueeze(sp_ov, axes=[0]).output(0)
    if len(end_points.shape) == 2:
        ep_ov = ov_opset.unsqueeze(ep_ov, axes=[0]).output(0)

    if data_format == "channels_first":
        images_ov = ov_opset.transpose(
            images_ov,
            ov_opset.constant([0, 2, 3, 1], Type.i32).output(0),
        ).output(0)

    images_ov = ov_opset.convert(images_ov, compute_type).output(0)
    sp_ov = ov_opset.convert(sp_ov, compute_type).output(0)
    ep_ov = ov_opset.convert(ep_ov, compute_type).output(0)

    transforms = _ov_compute_homography(sp_ov, ep_ov)

    shape_node = ov_opset.shape_of(images_ov, output_type=Type.i32).output(0)
    axis0 = ov_opset.constant(0, Type.i32).output(0)

    def dim(i):
        return ov_opset.gather(
            shape_node, ov_opset.constant(i, Type.i32).output(0), axis0
        ).output(0)

    B = dim(0)
    H = dim(1)
    W = dim(2)
    C = dim(3)

    H_f = ov_opset.convert(H, Type.f32).output(0)
    W_f = ov_opset.convert(W, Type.f32).output(0)
    zero_f = ov_opset.constant(0.0, Type.f32).output(0)
    one_f = ov_opset.constant(1.0, Type.f32).output(0)
    r_h = ov_opset.range(zero_f, H_f, one_f, output_type=Type.f32).output(
        0
    )  # [H]
    r_w = ov_opset.range(zero_f, W_f, one_f, output_type=Type.f32).output(
        0
    )  # [W]

    def p1d(scalar):
        return ov_opset.reshape(
            scalar, ov_opset.constant([1], Type.i32).output(0), False
        ).output(0)

    hw_shape = ov_opset.concat([p1d(H), p1d(W)], axis=0).output(0)
    # y: rows  [H, W]
    y = ov_opset.broadcast(
        ov_opset.reshape(
            r_h,
            ov_opset.concat(
                [p1d(H), ov_opset.constant([1], Type.i32).output(0)], axis=0
            ).output(0),
            False,
        ).output(0),
        hw_shape,
    ).output(0)
    # x: cols  [H, W]
    x = ov_opset.broadcast(
        ov_opset.reshape(
            r_w,
            ov_opset.concat(
                [ov_opset.constant([1], Type.i32).output(0), p1d(W)], axis=0
            ).output(0),
            False,
        ).output(0),
        hw_shape,
    ).output(0)

    neg1 = ov_opset.constant([-1], Type.i32).output(0)
    x_flat = ov_opset.reshape(x, neg1, False).output(0)  # [N]
    y_flat = ov_opset.reshape(y, neg1, False).output(0)  # [N]

    axis1 = ov_opset.constant(1, Type.i32).output(0)

    def h_col(i):
        return ov_opset.squeeze(
            ov_opset.gather(
                transforms, ov_opset.constant([i], Type.i32).output(0), axis1
            ).output(0),  # [B, 1]
            axes=[1],
        ).output(0)  # [B]

    a0, a1, a2 = h_col(0), h_col(1), h_col(2)
    a3, a4, a5 = h_col(3), h_col(4), h_col(5)
    a6, a7 = h_col(6), h_col(7)

    N_shape = ov_opset.shape_of(x_flat, output_type=Type.i32).output(0)
    BN_shape = ov_opset.concat(
        [
            ov_opset.reshape(
                B, ov_opset.constant([1], Type.i32).output(0), False
            ).output(0),
            N_shape,
        ],
        axis=0,
    ).output(0)

    def bcast(v):
        return ov_opset.broadcast(
            ov_opset.unsqueeze(v, axes=[1]).output(0), BN_shape
        ).output(0)

    x_bn = ov_opset.broadcast(
        ov_opset.unsqueeze(x_flat, axes=[0]).output(0), BN_shape
    ).output(0)
    y_bn = ov_opset.broadcast(
        ov_opset.unsqueeze(y_flat, axes=[0]).output(0), BN_shape
    ).output(0)

    # denom = a6*x + a7*y + 1
    one_bn = ov_opset.broadcast(
        ov_opset.constant(1.0, Type.f32).output(0), BN_shape
    ).output(0)
    denom = ov_opset.add(
        ov_opset.add(
            ov_opset.multiply(bcast(a6), x_bn).output(0),
            ov_opset.multiply(bcast(a7), y_bn).output(0),
        ).output(0),
        one_bn,
    ).output(0)

    # x_in = (a0*x + a1*y + a2) / denom
    x_in = ov_opset.divide(
        ov_opset.add(
            ov_opset.add(
                ov_opset.multiply(bcast(a0), x_bn).output(0),
                ov_opset.multiply(bcast(a1), y_bn).output(0),
            ).output(0),
            bcast(a2),
        ).output(0),
        denom,
    ).output(0)

    # y_in = (a3*x + a4*y + a5) / denom
    y_in = ov_opset.divide(
        ov_opset.add(
            ov_opset.add(
                ov_opset.multiply(bcast(a3), x_bn).output(0),
                ov_opset.multiply(bcast(a4), y_bn).output(0),
            ).output(0),
            bcast(a5),
        ).output(0),
        denom,
    ).output(0)

    bhw_shape = ov_opset.concat([p1d(B), p1d(H), p1d(W)], axis=0).output(0)
    y_in = ov_opset.reshape(y_in, bhw_shape, False).output(0)
    x_in = ov_opset.reshape(x_in, bhw_shape, False).output(0)

    C_f = ov_opset.convert(C, Type.f32).output(0)
    r_c = ov_opset.range(zero_f, C_f, one_f, output_type=Type.f32).output(
        0
    )  # [C]

    bhwc_shape = ov_opset.concat(
        [p1d(B), p1d(H), p1d(W), p1d(C)], axis=0
    ).output(0)

    y_in_bhwc = ov_opset.broadcast(
        ov_opset.unsqueeze(y_in, axes=[3]).output(0), bhwc_shape
    ).output(0)
    x_in_bhwc = ov_opset.broadcast(
        ov_opset.unsqueeze(x_in, axes=[3]).output(0), bhwc_shape
    ).output(0)
    chan_bhwc = ov_opset.broadcast(
        ov_opset.reshape(
            r_c,
            ov_opset.concat(
                [ov_opset.constant([1, 1, 1], Type.i32).output(0), p1d(C)],
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
                [p1d(B), ov_opset.constant([1, 1, 1], Type.i32).output(0)],
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
            ov_opset.unsqueeze(y_in_bhwc, axes=[0]).output(0),
            ov_opset.unsqueeze(x_in_bhwc, axes=[0]).output(0),
            ov_opset.unsqueeze(chan_bhwc, axes=[0]).output(0),
        ],
        axis=0,
    ).output(0)

    result = map_coordinates(
        OpenVINOKerasTensor(images_ov),
        OpenVINOKerasTensor(coords),
        order=AFFINE_TRANSFORM_INTERPOLATIONS[interpolation],
        fill_mode="constant",
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