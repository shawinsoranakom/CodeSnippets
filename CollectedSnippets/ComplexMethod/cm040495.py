def quantile(x, q, axis=None, method="linear", keepdims=False):
    x = get_ov_output(x)
    q_ov = get_ov_output(q)

    x_keras_type = ov_to_keras_type(x.get_element_type())
    compute_dtype = (
        config.floatx()
        if x_keras_type in ("int64", "bool")
        else dtypes.result_type(x_keras_type, float)
    )
    compute_ov_type = OPENVINO_DTYPES[compute_dtype]
    x = ov_opset.convert(x, compute_ov_type).output(0)
    q_f64 = ov_opset.convert(q_ov, Type.f64).output(0)
    q_rank = q_ov.get_partial_shape().rank.get_length()
    x_ndim = x.get_partial_shape().rank.get_length()

    y, norm_axis = _move_and_flatten_axes(axis, x_ndim, x)

    sorted_y = sort(OpenVINOKerasTensor(y)).output

    # Size of the last (sorted) dimension, needed for index computation
    y_ndim = y.get_partial_shape().rank.get_length()
    n_i32 = ov_opset.squeeze(
        ov_opset.gather(
            ov_opset.shape_of(y, Type.i32).output(0),
            ov_opset.constant([y_ndim - 1], Type.i32).output(0),
            ov_opset.constant(0, Type.i32).output(0),
        ).output(0),
        ov_opset.constant([0], Type.i32).output(0),
    ).output(0)

    # exact_idx = (n - 1) * q  in float64 for precision
    n_f64 = ov_opset.convert(n_i32, Type.f64).output(0)
    exact_idx = ov_opset.multiply(
        ov_opset.subtract(
            n_f64, ov_opset.constant(np.float64(1.0)).output(0)
        ).output(0),
        q_f64,
    ).output(0)

    zero_i32 = ov_opset.constant(np.int32(0)).output(0)
    n_minus1_i32 = ov_opset.subtract(
        n_i32, ov_opset.constant(np.int32(1)).output(0)
    ).output(0)
    last_ax = ov_opset.constant(y_ndim - 1, Type.i32).output(0)

    def _clamp_idx(f64_idx):
        i = ov_opset.convert(f64_idx, Type.i32).output(0)
        return ov_opset.minimum(
            ov_opset.maximum(i, zero_i32).output(0), n_minus1_i32
        ).output(0)

    def _gather(idx):
        return ov_opset.gather(sorted_y, idx, last_ax).output(0)

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

    # keepdims: insert size-1 dims before rotating q to front
    if keepdims:
        axes_to_add = (
            list(range(x_ndim)) if norm_axis is None else sorted(norm_axis)
        )
        for i in axes_to_add:
            gathered = ov_opset.unsqueeze(
                gathered, ov_opset.constant([i], Type.i32).output(0)
            ).output(0)

    # For 1-D q, rotate the q dim from last to first
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