def rnn(
    step_function,
    inputs,
    initial_states,
    go_backwards=False,
    mask=None,
    constants=None,
    unroll=False,
    input_length=None,
    time_major=False,
    zero_output_for_mask=False,
    return_all_outputs=True,
):
    def swap_batch_timestep(input_t):
        axes = list(range(len(input_t.shape)))
        axes[0], axes[1] = 1, 0
        perm_const = ov_opset.constant(axes, dtype=Type.i32).output(0)
        input_ov = get_ov_output(input_t)
        return OpenVINOKerasTensor(
            ov_opset.transpose(input_ov, perm_const).output(0)
        )

    if not time_major:
        inputs = tree.map_structure(swap_batch_timestep, inputs)
        if mask is not None:
            mask = swap_batch_timestep(mask)
    flattened_inputs = tree.flatten(inputs)
    input_0 = flattened_inputs[0]
    input_0_ov = get_ov_output(input_0)
    input_shape = ov_opset.shape_of(input_0_ov, Type.i32).output(0)
    time_steps = ov_opset.gather(
        input_shape,
        ov_opset.constant([0], dtype=Type.i32).output(0),
        ov_opset.constant(0, dtype=Type.i32).output(0),
    ).output(0)
    time_steps = ov_opset.squeeze(
        time_steps, ov_opset.constant([0], dtype=Type.i32).output(0)
    ).output(0)
    if mask is None and input_length is not None:
        input_len_ov = get_ov_output(input_length)
        if input_len_ov.get_partial_shape().rank.get_length() == 1:
            indices = ov_opset.range(
                ov_opset.constant(0, dtype=Type.i32).output(0),
                time_steps,
                ov_opset.constant(1, dtype=Type.i32).output(0),
                output_type=Type.i32,
            ).output(0)
            indices = ov_opset.unsqueeze(
                indices, ov_opset.constant([1], dtype=Type.i32).output(0)
            ).output(0)
            input_len_casted = ov_opset.convert(input_len_ov, Type.i32).output(
                0
            )
            input_len_expanded = ov_opset.unsqueeze(
                input_len_casted,
                ov_opset.constant([0], dtype=Type.i32).output(0),
            ).output(0)
            mask_bool = ov_opset.less(indices, input_len_expanded).output(0)
            mask = OpenVINOKerasTensor(mask_bool)
    if mask is not None:
        mask_ov = get_ov_output(mask)
        if mask_ov.get_element_type() != Type.boolean:
            mask_ov = ov_opset.convert(mask_ov, Type.boolean).output(0)
        pshape = mask_ov.get_partial_shape()
        rank = pshape.rank.get_length()
        if rank == 2:
            mask_ov = ov_opset.unsqueeze(
                mask_ov, ov_opset.constant([-1], dtype=Type.i32).output(0)
            ).output(0)
        mask = OpenVINOKerasTensor(mask_ov)
    if go_backwards:

        def reverse_time(x):
            x_ov = get_ov_output(x)
            start = ov_opset.constant([0], dtype=Type.i32).output(0)
            idx = ov_opset.range(
                ov_opset.subtract(
                    time_steps, ov_opset.constant(1, dtype=Type.i32).output(0)
                ).output(0),
                ov_opset.constant(-1, dtype=Type.i32).output(0),
                ov_opset.constant(-1, dtype=Type.i32).output(0),
                output_type=Type.i32,
            ).output(0)
            return OpenVINOKerasTensor(
                ov_opset.gather(x_ov, idx, start).output(0)
            )

        inputs = tree.map_structure(reverse_time, inputs)
        if mask is not None:
            mask = reverse_time(mask)
        flattened_inputs = tree.flatten(inputs)

    # If the time dimension is statically known, use the unrolled path.
    # The OV CPU TensorIterator plugin does not support Convolution ops
    # inside a Loop body, so ConvLSTM (and any cell using ops.conv) would
    # fail at compile time with the loop-based path.
    static_time_steps = None
    pshape_0 = input_0_ov.get_partial_shape()
    if pshape_0.rank.is_static and pshape_0.rank.get_length() >= 1:
        dim0 = pshape_0[0]
        if dim0.is_static:
            static_time_steps = dim0.get_length()

    if static_time_steps is not None:
        return _rnn_unrolled(
            step_function,
            inputs,
            initial_states,
            mask,
            constants,
            static_time_steps,
            time_major,
            zero_output_for_mask,
            return_all_outputs,
            swap_batch_timestep,
        )

    return _rnn_loop(
        step_function,
        inputs,
        initial_states,
        mask,
        constants,
        time_steps,
        time_major,
        zero_output_for_mask,
        return_all_outputs,
        swap_batch_timestep,
    )