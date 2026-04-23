def lstm(
    inputs,
    initial_h,
    initial_c,
    mask,
    kernel,
    recurrent_kernel,
    bias,
    activation,
    recurrent_activation,
    return_sequences=False,
    go_backwards=False,
    unroll=False,
):
    act_name = getattr(activation, "__name__", None)
    rec_act_name = getattr(recurrent_activation, "__name__", None)
    if not (
        act_name == "tanh"
        and rec_act_name == "sigmoid"
        and not unroll
        and bias is not None
        and mask is None
    ):
        raise NotImplementedError

    inputs_ov = get_ov_output(inputs)
    initial_h_ov = get_ov_output(initial_h)
    initial_c_ov = get_ov_output(initial_c)
    kernel_ov = get_ov_output(kernel)
    recurrent_kernel_ov = get_ov_output(recurrent_kernel)
    bias_ov = get_ov_output(bias)

    weight_type = kernel_ov.get_element_type()
    if inputs_ov.get_element_type() != weight_type:
        inputs_ov = ov_opset.convert(inputs_ov, weight_type).output(0)

    hidden_size = recurrent_kernel_ov.get_partial_shape()[0].get_length()

    k_data = _try_eval_constant(kernel_ov)
    r_data = _try_eval_constant(recurrent_kernel_ov)
    b_data = _try_eval_constant(bias_ov)
    if k_data is not None and r_data is not None and b_data is not None:
        # Pre-fold into numpy Constants so the CPU plugin sees Constant nodes
        # on the W, R, B ports of LSTMSequence (requires Constant or Parameter).
        dtype = str(k_data.dtype)
        # kernel [in,4h] -> [4h,in] reordered [i,f,c,o]->[f,i,c,o] -> [1,4h,in]
        k_np = _reorder_np(
            k_data.T, ["i", "f", "c", "o"], ["f", "i", "c", "o"], axis=0
        )
        w = _ov_const(k_np[np.newaxis], dtype)
        # recurrent_kernel [h, 4*h] -> [4*h, h] reordered -> [1, 4*h, h]
        r_np = _reorder_np(
            r_data.T, ["i", "f", "c", "o"], ["f", "i", "c", "o"], axis=0
        )
        r = _ov_const(r_np[np.newaxis], dtype)
        # bias [4*h] reordered -> [1, 4*h]
        b_np = _reorder_np(
            b_data, ["i", "f", "c", "o"], ["f", "i", "c", "o"], axis=0
        )
        b = _ov_const(b_np[np.newaxis], dtype)
    else:
        kt = ov_opset.transpose(
            kernel_ov,
            ov_opset.constant([1, 0], dtype=Type.i32).output(0),
        ).output(0)
        w = _reorder_gates(
            kt, ["i", "f", "c", "o"], ["f", "i", "c", "o"], axis=0
        )
        w = ov_opset.unsqueeze(
            w, ov_opset.constant([0], dtype=Type.i32).output(0)
        ).output(0)

        rt = ov_opset.transpose(
            recurrent_kernel_ov,
            ov_opset.constant([1, 0], dtype=Type.i32).output(0),
        ).output(0)
        r = _reorder_gates(
            rt, ["i", "f", "c", "o"], ["f", "i", "c", "o"], axis=0
        )
        r = ov_opset.unsqueeze(
            r, ov_opset.constant([0], dtype=Type.i32).output(0)
        ).output(0)

        b = _reorder_gates(
            bias_ov, ["i", "f", "c", "o"], ["f", "i", "c", "o"], axis=0
        )
        b = ov_opset.unsqueeze(
            b, ov_opset.constant([0], dtype=Type.i32).output(0)
        ).output(0)

    h0 = ov_opset.unsqueeze(
        initial_h_ov, ov_opset.constant([1], dtype=Type.i32).output(0)
    ).output(0)
    c0 = ov_opset.unsqueeze(
        initial_c_ov, ov_opset.constant([1], dtype=Type.i32).output(0)
    ).output(0)

    seq_lens = _seq_lengths(inputs_ov)
    direction = "reverse" if go_backwards else "forward"

    lstm_out = ov_opset.lstm_sequence(
        inputs_ov, h0, c0, seq_lens, w, r, b, hidden_size, direction
    )
    dir_axis = ov_opset.constant([1], dtype=Type.i32).output(0)
    all_outputs = ov_opset.squeeze(lstm_out.output(0), dir_axis).output(0)
    h_n = ov_opset.squeeze(lstm_out.output(1), dir_axis).output(0)
    c_n = ov_opset.squeeze(lstm_out.output(2), dir_axis).output(0)

    if go_backwards:
        shape = ov_opset.shape_of(all_outputs, Type.i32).output(0)
        time_len = ov_opset.gather(
            shape,
            ov_opset.constant(1, dtype=Type.i32).output(0),
            ov_opset.constant(0, dtype=Type.i32).output(0),
        ).output(0)
        idx = ov_opset.range(
            ov_opset.subtract(
                time_len, ov_opset.constant(1, dtype=Type.i32).output(0)
            ).output(0),
            ov_opset.constant(-1, dtype=Type.i32).output(0),
            ov_opset.constant(-1, dtype=Type.i32).output(0),
            output_type=Type.i32,
        ).output(0)
        all_outputs = ov_opset.gather(
            all_outputs,
            idx,
            ov_opset.constant(1, dtype=Type.i32).output(0),
        ).output(0)

    return (
        OpenVINOKerasTensor(h_n),
        OpenVINOKerasTensor(all_outputs),
        [OpenVINOKerasTensor(h_n), OpenVINOKerasTensor(c_n)],
    )