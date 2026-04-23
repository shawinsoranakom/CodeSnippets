def gru(
    inputs,
    initial_state,
    mask,
    kernel,
    recurrent_kernel,
    bias,
    activation,
    recurrent_activation,
    return_sequences=False,
    go_backwards=False,
    unroll=False,
    reset_after=True,
):
    act_name = getattr(activation, "__name__", None)
    rec_act_name = getattr(recurrent_activation, "__name__", None)
    if not (
        act_name == "tanh"
        and rec_act_name == "sigmoid"
        and not unroll
        and bias is not None
        and reset_after
        and mask is None
    ):
        raise NotImplementedError

    inputs_ov = get_ov_output(inputs)
    initial_state_ov = get_ov_output(initial_state)
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
        # on the W, R, B ports of GRUSequence (requires Constant or Parameter).
        dtype = str(k_data.dtype)
        # kernel [in, 3*h] -> [3*h, in] -> [1, 3*h, in]
        w = _ov_const(k_data.T[np.newaxis], dtype)
        # recurrent_kernel [h, 3*h] -> [3*h, h] -> [1, 3*h, h]
        r = _ov_const(r_data.T[np.newaxis], dtype)
        # Keras bias [2,3h]: row 0=[b_z,b_r,b_h], row 1=[rb_z,rb_r,rb_h]
        # OV gru_sequence (linear_before_reset=True) wants B [1, 4*h]:
        # [b_z+rb_z, b_r+rb_r, b_h, rb_h]
        b_in, b_rc = b_data[0], b_data[1]
        n = b_in.shape[0] // 3
        b_np = np.concatenate(
            [
                b_in[:n] + b_rc[:n],
                b_in[n : 2 * n] + b_rc[n : 2 * n],
                b_in[2 * n :],
                b_rc[2 * n :],
            ],
            axis=0,
        )
        b = _ov_const(b_np[np.newaxis], dtype)
    else:
        w = ov_opset.transpose(
            kernel_ov,
            ov_opset.constant([1, 0], dtype=Type.i32).output(0),
        ).output(0)
        w = ov_opset.unsqueeze(
            w, ov_opset.constant([0], dtype=Type.i32).output(0)
        ).output(0)

        r = ov_opset.transpose(
            recurrent_kernel_ov,
            ov_opset.constant([1, 0], dtype=Type.i32).output(0),
        ).output(0)
        r = ov_opset.unsqueeze(
            r, ov_opset.constant([0], dtype=Type.i32).output(0)
        ).output(0)

        # Keras bias [2, 3*units]: row 0 = input biases [b_z, b_r, b_h],
        # row 1 = recurrent biases [rb_z, rb_r, rb_h].
        # OV gru_sequence (linear_before_reset=True) wants B [1, 4*units]:
        # [b_z+rb_z, b_r+rb_r, b_h, rb_h]
        ax = ov_opset.constant(0, dtype=Type.i32).output(0)
        b_input = ov_opset.gather(
            bias_ov, ov_opset.constant(0, dtype=Type.i32).output(0), ax
        ).output(0)
        b_recur = ov_opset.gather(
            bias_ov, ov_opset.constant(1, dtype=Type.i32).output(0), ax
        ).output(0)
        split_ax = ov_opset.constant(0, dtype=Type.i32).output(0)
        b_in_parts = ov_opset.split(b_input, split_ax, 3).outputs()
        b_rc_parts = ov_opset.split(b_recur, split_ax, 3).outputs()
        b_z = ov_opset.add(b_in_parts[0], b_rc_parts[0]).output(0)
        b_r = ov_opset.add(b_in_parts[1], b_rc_parts[1]).output(0)
        b_h = b_in_parts[2]
        rb_h = b_rc_parts[2]
        b = ov_opset.concat([b_z, b_r, b_h, rb_h], axis=0).output(0)
        b = ov_opset.unsqueeze(
            b, ov_opset.constant([0], dtype=Type.i32).output(0)
        ).output(0)

    h0 = ov_opset.unsqueeze(
        initial_state_ov, ov_opset.constant([1], dtype=Type.i32).output(0)
    ).output(0)

    seq_lens = _seq_lengths(inputs_ov)
    direction = "reverse" if go_backwards else "forward"

    gru_out = ov_opset.gru_sequence(
        inputs_ov,
        h0,
        seq_lens,
        w,
        r,
        b,
        hidden_size,
        direction,
        linear_before_reset=True,
    )
    dir_axis = ov_opset.constant([1], dtype=Type.i32).output(0)
    all_outputs = ov_opset.squeeze(gru_out.output(0), dir_axis).output(0)
    h_n = ov_opset.squeeze(gru_out.output(1), dir_axis).output(0)

    if go_backwards:
        # OV direction="reverse" outputs Y in original time order
        # (Y[0]=fully-accumulated state). Keras go_backwards expects
        # Y[0]=state after first reversed step. Flip time axis to match.
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
        [OpenVINOKerasTensor(h_n)],
    )