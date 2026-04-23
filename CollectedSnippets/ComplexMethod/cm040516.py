def qr(x, mode="reduced"):
    if mode not in {"reduced", "complete"}:
        raise ValueError(
            "`mode` argument value not supported. "
            "Expected one of {'reduced', 'complete'}. "
            f"Received: mode={mode}"
        )
    x = convert_to_tensor(x)
    x_ov = get_ov_output(x)
    orig_type = x_ov.get_element_type()

    # Work in f32:
    #   f64 — constant-folding bug in OpenVINO CPU Loop evaluate (same as det())
    #   f16/bf16 — upcast to f32 for numerical stability in iterative
    #              Householder
    #   complex/other — not supported for QR; convert best-effort to f32
    if orig_type != Type.f32:
        x_ov = ov_opset.convert(x_ov, Type.f32).output(0)
    work_type = Type.f32

    rank = x_ov.get_partial_shape().rank.get_length()

    # Scalar and 1-D integer constants
    SLICE_END = 2**30  # large sentinel for "slice to end of dimension"

    zero_s = ov_opset.constant(0, Type.i32).output(0)
    one_s = ov_opset.constant(1, Type.i32).output(0)
    zero_1d = ov_opset.constant([0], Type.i32).output(0)
    one_1d = ov_opset.constant([1], Type.i32).output(0)
    large_1d = ov_opset.constant([SLICE_END], Type.i32).output(0)
    axes012 = ov_opset.constant([0, 1, 2], Type.i32).output(0)
    step111 = ov_opset.constant([1, 1, 1], Type.i32).output(0)

    x_shape = ov_opset.shape_of(x_ov, output_type="i32").output(0)
    m_1d = ov_opset.gather(
        x_shape, ov_opset.constant([-2], Type.i32), zero_s
    ).output(0)
    n_1d = ov_opset.gather(
        x_shape, ov_opset.constant([-1], Type.i32), zero_s
    ).output(0)
    m_s = ov_opset.squeeze(m_1d, zero_s).output(0)
    n_s = ov_opset.squeeze(n_1d, zero_s).output(0)

    # Flatten batch dims → [B, M, N]
    if rank == 2:
        batch_1d = ov_opset.constant([1], Type.i32).output(0)
    else:
        batch_shape = ov_opset.slice(
            x_shape,
            zero_1d,
            ov_opset.constant([-2], Type.i32),
            one_1d,
            zero_1d,
        ).output(0)
        batch_s = ov_opset.reduce_prod(batch_shape, zero_s, False).output(0)
        batch_1d = ov_opset.unsqueeze(batch_s, zero_s).output(0)

    flat_shape = ov_opset.concat([batch_1d, m_1d, n_1d], 0).output(0)
    x_flat = ov_opset.reshape(x_ov, flat_shape, False).output(0)

    # K = min(M, N) — number of Householder steps
    k_s = ov_opset.minimum(m_s, n_s).output(0)

    # Q = eye(M) broadcast to [B, M, M],  R = x_flat [B, M, N]
    range_m = ov_opset.range(zero_s, m_s, one_s, output_type=Type.i32).output(0)
    eye_m = ov_opset.one_hot(
        range_m,
        m_s,
        ov_opset.constant(1.0, work_type),
        ov_opset.constant(0.0, work_type),
        axis=-1,
    ).output(0)  # [M, M]
    Q_init = ov_opset.broadcast(
        eye_m, ov_opset.concat([batch_1d, m_1d, m_1d], 0).output(0)
    ).output(0)  # [B, M, M]

    # ---- Householder loop ----
    loop = ov_opset.loop(k_s, ov_opset.constant(True, Type.boolean).output(0))

    R_param = ov_opset.parameter(x_flat.get_partial_shape(), work_type, "R")
    Q_param = ov_opset.parameter(Q_init.get_partial_shape(), work_type, "Q")
    k_param = ov_opset.parameter([], Type.i32, "k")

    R_body = R_param.output(0)
    Q_body = Q_param.output(0)
    k_body = k_param.output(0)
    k_1d = ov_opset.unsqueeze(k_body, zero_s).output(0)  # scalar → [1]

    # sub_R = R[:, k:, k:]  →  [B, sub_m, sub_n]
    sub_R = ov_opset.slice(
        R_body,
        ov_opset.concat([zero_1d, k_1d, k_1d], 0).output(0),
        ov_opset.concat([large_1d, large_1d, large_1d], 0).output(0),
        step111,
        axes012,
    ).output(0)

    # x_col = sub_R[:, :, 0]  →  [B, sub_m]
    x_col = ov_opset.gather(
        sub_R, ov_opset.constant(0, Type.i32), ov_opset.constant(2, Type.i32)
    ).output(0)

    # alpha = -sign(x_col[:, 0]) * ||x_col||
    x0 = ov_opset.gather(x_col, ov_opset.constant(0, Type.i32), one_s).output(0)
    sign_x0 = ov_opset.sign(x0).output(0)
    zero_f = ov_opset.constant(0.0, work_type).output(0)
    one_f = ov_opset.constant(1.0, work_type).output(0)
    sign_x0 = ov_opset.select(
        ov_opset.equal(sign_x0, zero_f), one_f, sign_x0
    ).output(0)
    norm_x = ov_opset.sqrt(
        ov_opset.reduce_sum(
            ov_opset.multiply(x_col, x_col).output(0), one_s, keep_dims=False
        ).output(0)
    ).output(0)
    alpha = ov_opset.negative(
        ov_opset.multiply(sign_x0, norm_x).output(0)
    ).output(0)  # [B]

    # Householder vector: v = x_col - alpha * e_0  (one-hot at position 0)
    # Use one_hot so v keeps the same shape as x_col → shape inference stays
    # clean.
    x_col_sh = ov_opset.shape_of(x_col, output_type="i32").output(0)
    sub_m_from_col = ov_opset.gather(x_col_sh, one_s, zero_s).output(0)
    e0 = ov_opset.one_hot(
        ov_opset.constant([0], Type.i32).output(0),
        sub_m_from_col,
        one_f,
        zero_f,
        axis=-1,
    ).output(0)  # [1, sub_m]
    alpha_2d = ov_opset.unsqueeze(alpha, one_s).output(0)  # [B, 1]
    v = ov_opset.subtract(
        x_col, ov_opset.multiply(alpha_2d, e0).output(0)
    ).output(0)  # [B, sub_m]

    # v_hat = v / ||v||
    norm_v = ov_opset.sqrt(
        ov_opset.reduce_sum(
            ov_opset.multiply(v, v).output(0), one_s, keep_dims=True
        ).output(0)
    ).output(0)  # [B, 1]
    eps = ov_opset.constant(1e-12, work_type).output(0)
    v_hat = ov_opset.divide(v, ov_opset.maximum(norm_v, eps).output(0)).output(
        0
    )

    # When sub_m == 1 the LAPACK convention is tau=0 (identity reflector).
    # Zero out v_hat so the Householder step is a no-op for that iteration.
    is_trivial = ov_opset.equal(
        sub_m_from_col, ov_opset.constant(1, Type.i32).output(0)
    ).output(0)  # bool scalar
    scale = ov_opset.subtract(
        one_f,
        ov_opset.convert(is_trivial, work_type).output(0),
    ).output(0)  # 1.0 normally, 0.0 when sub_m==1
    v_hat = ov_opset.multiply(v_hat, scale).output(0)

    v_col = ov_opset.unsqueeze(v_hat, ov_opset.constant(2, Type.i32)).output(
        0
    )  # [B, sub_m, 1]
    v_row = ov_opset.unsqueeze(v_hat, one_s).output(0)  # [B, 1, sub_m]

    two_f = ov_opset.constant(2.0, work_type).output(0)

    # Apply H to sub_R: sub_R -= 2 * v_col @ (v_row @ sub_R)
    vTR = ov_opset.matmul(v_row, sub_R, False, False).output(0)  # [B, 1, sub_n]
    sub_R_new = ov_opset.subtract(
        sub_R,
        ov_opset.multiply(
            two_f, ov_opset.matmul(v_col, vTR, False, False).output(0)
        ).output(0),
    ).output(0)  # [B, sub_m, sub_n]

    # Apply H to Q columns k..: Q[:, :, k:] -= 2 * (Q[:, :, k:] @ v_col) @ v_row
    Q_sub = ov_opset.slice(
        Q_body,
        ov_opset.concat([zero_1d, zero_1d, k_1d], 0).output(0),
        ov_opset.concat([large_1d, large_1d, large_1d], 0).output(0),
        step111,
        axes012,
    ).output(0)  # [B, M, sub_m]
    Qv = ov_opset.matmul(Q_sub, v_col, False, False).output(0)  # [B, M, 1]
    Q_sub_new = ov_opset.subtract(
        Q_sub,
        ov_opset.multiply(
            two_f, ov_opset.matmul(Qv, v_row, False, False).output(0)
        ).output(0),
    ).output(0)  # [B, M, sub_m]

    # Reconstruct R_next: keep top rows and left cols, replace bottom-right
    # block
    top_R = ov_opset.slice(
        R_body,
        ov_opset.concat([zero_1d, zero_1d, zero_1d], 0).output(0),
        ov_opset.concat([large_1d, k_1d, large_1d], 0).output(0),
        step111,
        axes012,
    ).output(0)  # [B, k, N]
    left_bot_R = ov_opset.slice(
        R_body,
        ov_opset.concat([zero_1d, k_1d, zero_1d], 0).output(0),
        ov_opset.concat([large_1d, large_1d, k_1d], 0).output(0),
        step111,
        axes012,
    ).output(0)  # [B, sub_m, k]
    R_next = ov_opset.concat(
        [top_R, ov_opset.concat([left_bot_R, sub_R_new], 2).output(0)],
        1,
    ).output(0)  # [B, M, N]

    # Reconstruct Q_next: keep left cols, replace right cols
    left_Q = ov_opset.slice(
        Q_body,
        ov_opset.concat([zero_1d, zero_1d, zero_1d], 0).output(0),
        ov_opset.concat([large_1d, large_1d, k_1d], 0).output(0),
        step111,
        axes012,
    ).output(0)  # [B, M, k]
    Q_next = ov_opset.concat([left_Q, Q_sub_new], 2).output(0)  # [B, M, M]

    cond_next = ov_opset.constant(True, Type.boolean).output(0)
    k_next = ov_opset.add(k_body, one_s).output(0)

    body_model = ov.Model(
        [cond_next, R_next, Q_next, k_next],
        [R_param, Q_param, k_param],
        "householder_qr",
    )
    loop.set_function(body_model)
    loop.set_special_body_ports([-1, 0])

    loop.set_merged_input(R_param, x_flat, R_next)
    loop.set_merged_input(Q_param, Q_init, Q_next)
    loop.set_merged_input(
        k_param, ov_opset.constant(0, Type.i32).output(0), k_next
    )

    R_out = loop.get_iter_value(R_next, -1)
    Q_out = loop.get_iter_value(Q_next, -1)

    # Reshape immediately after the loop to restore concrete shape information
    # (loop body slices with dynamic k cause output shape to become dynamic).
    Q_out = ov_opset.reshape(
        Q_out, ov_opset.concat([batch_1d, m_1d, m_1d], 0).output(0), False
    ).output(0)  # [B, M, M]
    R_out = ov_opset.reshape(
        R_out, ov_opset.concat([batch_1d, m_1d, n_1d], 0).output(0), False
    ).output(0)  # [B, M, N]

    k_1d_out = ov_opset.unsqueeze(k_s, zero_s).output(0)

    # Trim to requested mode: Q [B,M,K], R [B,K,N]
    # (complete keeps [B,M,M],[B,M,N])
    if mode == "reduced":
        Q_out = ov_opset.slice(
            Q_out,
            ov_opset.constant([0, 0, 0], Type.i32).output(0),
            ov_opset.concat([large_1d, large_1d, k_1d_out], 0).output(0),
            step111,
            axes012,
        ).output(0)  # [B, M, K]
        R_out = ov_opset.slice(
            R_out,
            ov_opset.constant([0, 0, 0], Type.i32).output(0),
            ov_opset.concat([large_1d, k_1d_out, large_1d], 0).output(0),
            step111,
            axes012,
        ).output(0)  # [B, K, N]

    # Restore original batch shape using reshape (not squeeze) to keep
    # concrete dims
    if rank == 2:
        if mode == "reduced":
            q_shape_2d = ov_opset.concat([m_1d, k_1d_out], 0).output(0)
            r_shape_2d = ov_opset.concat([k_1d_out, n_1d], 0).output(0)
        else:
            q_shape_2d = ov_opset.concat([m_1d, m_1d], 0).output(0)
            r_shape_2d = ov_opset.concat([m_1d, n_1d], 0).output(0)
        Q_out = ov_opset.reshape(Q_out, q_shape_2d, False).output(0)
        R_out = ov_opset.reshape(R_out, r_shape_2d, False).output(0)
    elif rank > 2:
        batch_shape_node = ov_opset.slice(
            ov_opset.shape_of(x_ov, output_type="i32").output(0),
            zero_1d,
            ov_opset.constant([-2], Type.i32),
            one_1d,
            zero_1d,
        ).output(0)
        q_last = ov_opset.gather(
            ov_opset.shape_of(Q_out, output_type="i32").output(0),
            ov_opset.constant([-1], Type.i32),
            zero_s,
        ).output(0)
        r_second_last = ov_opset.gather(
            ov_opset.shape_of(R_out, output_type="i32").output(0),
            ov_opset.constant([-2], Type.i32),
            zero_s,
        ).output(0)
        Q_out = ov_opset.reshape(
            Q_out,
            ov_opset.concat([batch_shape_node, m_1d, q_last], 0).output(0),
            False,
        ).output(0)
        R_out = ov_opset.reshape(
            R_out,
            ov_opset.concat([batch_shape_node, r_second_last, n_1d], 0).output(
                0
            ),
            False,
        ).output(0)

    if orig_type != work_type:
        Q_out = ov_opset.convert(Q_out, orig_type).output(0)
        R_out = ov_opset.convert(R_out, orig_type).output(0)

    return OpenVINOKerasTensor(Q_out), OpenVINOKerasTensor(R_out)