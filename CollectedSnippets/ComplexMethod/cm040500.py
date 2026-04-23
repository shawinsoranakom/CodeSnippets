def slogdet(x):
    x = convert_to_tensor(x)
    x_ov = get_ov_output(x)
    x_ov_type = x_ov.get_element_type()

    # Cast integer/boolean inputs to float
    if x_ov_type.is_integral() or x_ov_type == Type.boolean:
        float_type = OPENVINO_DTYPES[config.floatx()]
        x_ov = ov_opset.convert(x_ov, float_type).output(0)
        x_ov_type = x_ov.get_element_type()

    # Promote to result type (e.g. float32 -> float64 if needed)
    keras_type = ov_to_keras_type(x_ov_type)
    result_ov_type = OPENVINO_DTYPES[dtypes.result_type(keras_type, float)]
    if x_ov_type != result_ov_type:
        x_ov = ov_opset.convert(x_ov, result_ov_type).output(0)
        x_ov_type = result_ov_type

    x_shape = x_ov.get_partial_shape()
    x_rank = len(x_shape)
    n = x_shape[-1].get_length()

    # Flatten batch dims: (..., n, n) -> (batch, n, n)
    flat_shape = ov_opset.constant([-1, n, n], Type.i32).output(0)
    x_batched = ov_opset.reshape(x_ov, flat_shape, False).output(0)

    batch_shape = ov_opset.shape_of(x_batched, Type.i32).output(0)
    batch_size = ov_opset.gather(
        batch_shape,
        ov_opset.constant([0], Type.i32).output(0),
        ov_opset.constant(0, Type.i32).output(0),
    ).output(0)

    zero = ov_opset.constant(0.0, x_ov_type).output(0)
    one = ov_opset.constant(1.0, x_ov_type).output(0)
    two = ov_opset.constant(2.0, x_ov_type).output(0)

    # Accumulators — one value per batch element
    log_abs_det = ov_opset.broadcast(zero, batch_size).output(0)
    sign_det = ov_opset.broadcast(one, batch_size).output(0)

    row_axis = ov_opset.constant(1, Type.i32).output(0)
    col_axis = ov_opset.constant(2, Type.i32).output(0)

    # LU decomposition with partial pivoting
    for k in range(n):
        # Find pivot row: max |value| in column k, from row k downward
        col_k = ov_opset.gather(
            x_batched, ov_opset.constant(k, Type.i32).output(0), col_axis
        ).output(0)
        abs_col_k = ov_opset.absolute(col_k).output(0)

        # Slice rows [k:n] of the column
        abs_col_k_sub = ov_opset.slice(
            abs_col_k,
            ov_opset.constant([0, k], Type.i32).output(0),
            ov_opset.constant([2**30, n], Type.i32).output(0),
            ov_opset.constant([1, 1], Type.i32).output(0),
            ov_opset.constant([0, 1], Type.i32).output(0),
        ).output(0)

        topk_result = ov_opset.topk(
            abs_col_k_sub,
            ov_opset.constant(1, Type.i32).output(0),
            axis=1,
            mode="max",
            sort="none",
        )
        local_max_idx = ov_opset.squeeze(
            ov_opset.convert(topk_result.output(1), Type.i32).output(0),
            ov_opset.constant([1], Type.i32).output(0),
        ).output(0)

        # Absolute pivot row index (local index is relative to row k)
        pivot_row = ov_opset.add(
            local_max_idx, ov_opset.constant(k, Type.i32).output(0)
        ).output(0)

        # Track sign change caused by row swap
        swap_needed = ov_opset.not_equal(
            pivot_row, ov_opset.constant(k, Type.i32).output(0)
        ).output(0)
        swap_needed_f = ov_opset.convert(swap_needed, x_ov_type).output(0)
        # sign_flip = 1 - 2*swap_needed_f  →  no swap: +1, swap: -1
        sign_flip = ov_opset.subtract(
            ov_opset.broadcast(one, batch_size).output(0),
            ov_opset.multiply(two, swap_needed_f).output(0),
        ).output(0)
        sign_det = ov_opset.multiply(sign_det, sign_flip).output(0)

        # Swap row k with pivot_row
        row_k = ov_opset.gather(
            x_batched, ov_opset.constant([k], Type.i32).output(0), row_axis
        ).output(0)
        pivot_row_2d = ov_opset.unsqueeze(
            pivot_row, ov_opset.constant([1], Type.i32).output(0)
        ).output(0)
        pivot_row_data = ov_opset.gather(
            x_batched, pivot_row_2d, row_axis, batch_dims=1
        ).output(0)

        # Write pivot row data into position k
        x_batched = ov_opset.scatter_update(
            x_batched,
            ov_opset.constant([k], Type.i32).output(0),
            pivot_row_data,
            row_axis,
        ).output(0)

        # Write old row k into position pivot_row (mask-based scatter)
        all_row_indices = ov_opset.unsqueeze(
            ov_opset.range(
                ov_opset.constant(0, Type.i32).output(0),
                ov_opset.constant(n, Type.i32).output(0),
                ov_opset.constant(1, Type.i32).output(0),
                output_type=Type.i32,
            ).output(0),
            ov_opset.constant([0, 2], Type.i32).output(0),
        ).output(0)

        pivot_row_3d = ov_opset.unsqueeze(
            pivot_row_2d, ov_opset.constant([2], Type.i32).output(0)
        ).output(0)
        swap_mask = ov_opset.equal(all_row_indices, pivot_row_3d).output(0)
        row_k_tiled = ov_opset.broadcast(
            row_k, ov_opset.shape_of(x_batched, Type.i32).output(0)
        ).output(0)
        x_batched = ov_opset.select(swap_mask, row_k_tiled, x_batched).output(0)

        # Extract pivot element and accumulate log|det| and sign
        k_idx = ov_opset.constant([k], Type.i32).output(0)
        pivot_row_cur = ov_opset.gather(x_batched, k_idx, row_axis).output(0)
        pivot_elem = ov_opset.gather(pivot_row_cur, k_idx, col_axis).output(0)
        pivot_scalar = ov_opset.squeeze(
            pivot_elem, ov_opset.constant([1, 2], Type.i32).output(0)
        ).output(0)

        abs_pivot = ov_opset.absolute(pivot_scalar).output(0)
        safe_abs = ov_opset.maximum(
            abs_pivot, ov_opset.constant(1e-38, x_ov_type).output(0)
        ).output(0)
        log_abs_det = ov_opset.add(
            log_abs_det, ov_opset.log(safe_abs).output(0)
        ).output(0)
        sign_det = ov_opset.multiply(
            sign_det, ov_opset.sign(pivot_scalar).output(0)
        ).output(0)

        # Protect against division by zero during elimination
        safe_pivot = ov_opset.select(
            ov_opset.equal(
                pivot_elem, ov_opset.constant(0.0, x_ov_type).output(0)
            ).output(0),
            ov_opset.constant(1.0, x_ov_type).output(0),
            pivot_elem,
        ).output(0)

        # Gaussian elimination: zero out entries below pivot
        for i in range(k + 1, n):
            i_idx = ov_opset.constant([i], Type.i32).output(0)
            row_i = ov_opset.gather(x_batched, i_idx, row_axis).output(0)
            elem_ik = ov_opset.gather(row_i, k_idx, col_axis).output(0)
            multiplier = ov_opset.divide(elem_ik, safe_pivot).output(0)
            row_i_new = ov_opset.subtract(
                row_i, ov_opset.multiply(multiplier, pivot_row_cur).output(0)
            ).output(0)
            x_batched = ov_opset.scatter_update(
                x_batched, i_idx, row_i_new, row_axis
            ).output(0)

    # For singular matrices: sign=0, logabsdet=-inf
    is_singular = ov_opset.equal(
        sign_det, ov_opset.broadcast(zero, batch_size).output(0)
    ).output(0)
    neg_inf = ov_opset.constant(float("-inf"), x_ov_type).output(0)
    log_abs_det = ov_opset.select(
        is_singular,
        ov_opset.broadcast(neg_inf, batch_size).output(0),
        log_abs_det,
    ).output(0)

    # Reshape outputs back to batch shape (drop last two dims)
    if x_rank > 2:
        batch_dims = [x_shape[i].get_length() for i in range(x_rank - 2)]
        out_shape = ov_opset.constant(batch_dims, Type.i32).output(0)
    else:
        out_shape = ov_opset.constant([], Type.i32).output(0)

    sign_result = ov_opset.reshape(sign_det, out_shape, False).output(0)
    logabsdet_result = ov_opset.reshape(log_abs_det, out_shape, False).output(0)

    return OpenVINOKerasTensor(sign_result), OpenVINOKerasTensor(
        logabsdet_result
    )