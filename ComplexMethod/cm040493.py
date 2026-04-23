def nanquantile(x, q, axis=None, method="linear", keepdims=False):
    # conversion to f32 due to https://github.com/openvinotoolkit/openvino/issues/34138
    if isinstance(x, np.ndarray) and x.dtype == np.float64:
        x = x.astype(np.float32)
    x = get_ov_output(x)
    q_ov = get_ov_output(q)
    x_type = x.get_element_type()
    if x_type == Type.f64:
        # conversion to f32 due to https://github.com/openvinotoolkit/openvino/issues/34138
        x = ov_opset.convert(x, Type.f32).output(0)
        x_type = Type.f32

    if x_type.is_integral() or x_type == Type.boolean:
        return quantile(
            OpenVINOKerasTensor(x),
            q,
            axis=axis,
            method=method,
            keepdims=keepdims,
        )

    x_keras_type = ov_to_keras_type(x_type)
    compute_dtype = dtypes.result_type(x_keras_type, float)
    compute_ov_type = OPENVINO_DTYPES[compute_dtype]
    x = ov_opset.convert(x, compute_ov_type).output(0)
    q_f64 = ov_opset.convert(q_ov, Type.f64).output(0)
    q_rank = q_ov.get_partial_shape().rank.get_length()
    x_ndim = x.get_partial_shape().rank.get_length()

    nan_mask = ov_opset.is_nan(x).output(0)
    pos_inf = ov_opset.convert(
        ov_opset.constant(np.array(np.inf, dtype=np.float32)).output(0),
        compute_ov_type,
    ).output(0)
    x_no_nan = ov_opset.select(nan_mask, pos_inf, x).output(0)

    y, nan_mask_flat, norm_axis = _move_and_flatten_axes(
        axis, x_ndim, x_no_nan, nan_mask
    )

    sorted_y = sort(OpenVINOKerasTensor(y)).output
    y_ndim = y.get_partial_shape().rank.get_length()

    not_nan_int = ov_opset.convert(
        ov_opset.logical_not(nan_mask_flat).output(0), Type.i32
    ).output(0)
    n_valid_i32 = ov_opset.reduce_sum(
        not_nan_int,
        ov_opset.constant([y_ndim - 1], Type.i32).output(0),
        False,
    ).output(0)
    all_nan = ov_opset.equal(
        n_valid_i32, ov_opset.constant(np.int32(0)).output(0)
    ).output(0)

    n_minus1_f64 = ov_opset.subtract(
        ov_opset.convert(n_valid_i32, Type.f64).output(0),
        ov_opset.constant(np.float64(1.0)).output(0),
    ).output(0)
    zero_i32 = ov_opset.constant(np.int32(0)).output(0)
    n_minus1_i32 = ov_opset.subtract(
        n_valid_i32, ov_opset.constant(np.int32(1)).output(0)
    ).output(0)
    if q_rank > 0:
        trailing = ov_opset.constant([-1], Type.i32).output(0)
        n_minus1_f64 = ov_opset.unsqueeze(n_minus1_f64, trailing).output(0)
        n_minus1_i32 = ov_opset.unsqueeze(n_minus1_i32, trailing).output(0)
    exact_idx = ov_opset.multiply(n_minus1_f64, q_f64).output(0)

    def _clamp_idx(f64_idx):
        i = ov_opset.convert(f64_idx, Type.i32).output(0)
        return ov_opset.minimum(
            ov_opset.maximum(i, zero_i32).output(0), n_minus1_i32
        ).output(0)

    sorted_y_tensor = OpenVINOKerasTensor(sorted_y)

    def _gather(idx):
        if q_rank == 0:
            idx_exp = ov_opset.unsqueeze(
                idx, ov_opset.constant([-1], Type.i32).output(0)
            ).output(0)
            result = take_along_axis(
                sorted_y_tensor, OpenVINOKerasTensor(idx_exp), axis=y_ndim - 1
            ).output
            return ov_opset.squeeze(
                result, ov_opset.constant([y_ndim - 1], Type.i32).output(0)
            ).output(0)
        else:
            return take_along_axis(
                sorted_y_tensor, OpenVINOKerasTensor(idx), axis=y_ndim - 1
            ).output

    lo_idx = _clamp_idx(ov_opset.floor(exact_idx).output(0))
    hi_idx = _clamp_idx(ov_opset.ceiling(exact_idx).output(0))

    if method == "lower":
        gathered = _gather(lo_idx)
    elif method == "higher":
        gathered = _gather(hi_idx)
    elif method == "nearest":
        gathered = _gather(
            _clamp_idx(ov_opset.round(exact_idx, "half_to_even").output(0))
        )
    elif method == "midpoint":
        two = ov_opset.convert(
            ov_opset.constant(np.float32(2.0)).output(0), compute_ov_type
        ).output(0)
        gathered = ov_opset.divide(
            ov_opset.add(_gather(lo_idx), _gather(hi_idx)).output(0), two
        ).output(0)
    else:  # linear
        # preserve_gradients: ensure interp_lo_idx < interp_hi_idx
        one_i32 = ov_opset.constant(np.int32(1)).output(0)
        interp_lo_idx = ov_opset.maximum(
            ov_opset.subtract(hi_idx, one_i32).output(0), zero_i32
        ).output(0)
        interp_hi_idx = ov_opset.minimum(
            ov_opset.add(interp_lo_idx, one_i32).output(0), n_minus1_i32
        ).output(0)
        frac = ov_opset.convert(
            ov_opset.subtract(
                ov_opset.convert(interp_hi_idx, Type.f64).output(0), exact_idx
            ).output(0),
            compute_ov_type,
        ).output(0)
        one_val = ov_opset.convert(
            ov_opset.constant(np.float32(1.0)).output(0), compute_ov_type
        ).output(0)
        gathered = ov_opset.add(
            ov_opset.multiply(
                _gather(interp_hi_idx),
                ov_opset.subtract(one_val, frac).output(0),
            ).output(0),
            ov_opset.multiply(_gather(interp_lo_idx), frac).output(0),
        ).output(0)

    nan_val = ov_opset.convert(
        ov_opset.constant(np.array(np.nan, dtype=np.float32)).output(0),
        compute_ov_type,
    ).output(0)
    if q_rank > 0:
        all_nan = ov_opset.unsqueeze(
            all_nan, ov_opset.constant([-1], Type.i32).output(0)
        ).output(0)
    gathered = ov_opset.select(all_nan, nan_val, gathered).output(0)

    if keepdims:
        axes_to_add = (
            list(range(x_ndim)) if norm_axis is None else sorted(norm_axis)
        )
        for i in axes_to_add:
            gathered = ov_opset.unsqueeze(
                gathered, ov_opset.constant([i], Type.i32).output(0)
            ).output(0)

    if q_rank > 0:
        g_ndim = gathered.get_partial_shape().rank.get_length()
        if g_ndim >= 2:
            gathered = ov_opset.transpose(
                gathered,
                ov_opset.constant(
                    [g_ndim - 1] + list(range(g_ndim - 1)), Type.i32
                ).output(0),
            ).output(0)

    return OpenVINOKerasTensor(gathered)