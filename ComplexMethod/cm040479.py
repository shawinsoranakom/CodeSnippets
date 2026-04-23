def cumprod(x, axis=None, dtype=None):
    x = get_ov_output(x)
    x_type = x.get_element_type()

    # Determine output dtype following numpy backend logic
    if dtype is not None:
        ov_type = OPENVINO_DTYPES[standardize_dtype(dtype)]
        if ov_type == Type.boolean:
            ov_type = Type.i32
    else:
        ov_type = x_type
        if ov_type == Type.boolean:
            ov_type = Type.i32

    # Convert boolean to int32 for computation
    if x_type == Type.boolean:
        x = ov_opset.convert(x, Type.i32).output(0)
        x_type = Type.i32

    compute_as_float = False
    if x_type.is_integral():
        compute_dtype = Type.f32
        x = ov_opset.convert(x, compute_dtype).output(0)
        compute_as_float = True
    else:
        compute_dtype = x_type

    x, axis = _resolve_axis(x, axis)

    signs = ov_opset.sign(x).output(0)

    is_zero_sign = ov_opset.equal(
        signs, ov_opset.constant(0, compute_dtype)
    ).output(0)
    signs_no_zeros = ov_opset.select(
        is_zero_sign, ov_opset.constant(1, compute_dtype), signs
    ).output(0)

    is_negative = ov_opset.less(
        signs_no_zeros, ov_opset.constant(0, compute_dtype)
    ).output(0)
    num_negatives = ov_opset.cumsum(
        ov_opset.convert(is_negative, Type.i32), axis
    ).output(0)
    is_odd = ov_opset.mod(num_negatives, ov_opset.constant(2, Type.i32)).output(
        0
    )

    cum_sign = ov_opset.subtract(
        ov_opset.constant(1, Type.i32),
        ov_opset.multiply(ov_opset.constant(2, Type.i32), is_odd),
    ).output(0)
    cum_sign = ov_opset.convert(cum_sign, compute_dtype).output(0)

    abs_x = ov_opset.absolute(x).output(0)
    is_zero_abs = ov_opset.equal(
        abs_x, ov_opset.constant(0, compute_dtype)
    ).output(0)
    abs_x_safe = ov_opset.select(
        is_zero_abs, ov_opset.constant(1, compute_dtype), abs_x
    ).output(0)

    log_abs_x = ov_opset.log(abs_x_safe).output(0)
    cumsum_log_abs = ov_opset.cumsum(log_abs_x, axis).output(0)
    cumprod_abs = ov_opset.exp(cumsum_log_abs).output(0)

    result = ov_opset.multiply(cumprod_abs, cum_sign).output(0)

    is_zero = ov_opset.equal(x, ov_opset.constant(0, compute_dtype)).output(0)
    has_zero_before = ov_opset.cumsum(
        ov_opset.convert(is_zero, Type.i32), axis
    ).output(0)
    zero_mask = ov_opset.equal(
        has_zero_before, ov_opset.constant(0, Type.i32)
    ).output(0)
    result = ov_opset.multiply(
        result, ov_opset.convert(zero_mask, compute_dtype)
    ).output(0)

    if compute_as_float and ov_type.is_integral():
        result = ov_opset.round(result).output(0)

    if result.get_element_type() != ov_type:
        result = ov_opset.convert(result, ov_type).output(0)

    return OpenVINOKerasTensor(result)