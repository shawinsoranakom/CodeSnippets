def _rnn_unrolled(
    step_function,
    inputs,
    initial_states,
    mask,
    constants,
    num_time_steps,
    time_major,
    zero_output_for_mask,
    return_all_outputs,
    swap_batch_timestep,
):
    """Unrolled RNN: iterate time steps in Python, producing a flat OV graph
    with no Loop op. Required when the cell contains ops (e.g. Convolution)
    that the OV CPU TensorIterator plugin cannot execute inside a loop body.
    """
    constants = constants or []
    flattened_constants = tree.flatten(constants)

    axis_0 = ov_opset.constant(0, dtype=Type.i32).output(0)

    def _slice_at(x, t_const):
        x_ov = get_ov_output(x)
        return OpenVINOKerasTensor(
            ov_opset.gather(x_ov, t_const, axis_0).output(0)
        )

    # Build constant wrappers for invariant inputs once, outside the time loop.
    constants_ov = [
        OpenVINOKerasTensor(get_ov_output(c)) for c in flattened_constants
    ]

    states = list(initial_states)
    successive_outputs = []
    last_output = None

    for t in range(num_time_steps):
        t_const = ov_opset.constant(t, dtype=Type.i32).output(0)
        inp_t = tree.map_structure(lambda x: _slice_at(x, t_const), inputs)
        output_t, new_states = step_function(
            inp_t, tuple(states) + tuple(constants_ov)
        )
        if not tree.is_nested(new_states):
            new_states = [new_states]

        if mask is not None:
            mask_t_ov = get_ov_output(_slice_at(mask, t_const))
            flat_new = tree.flatten(new_states)
            flat_old = tree.flatten(states)
            masked_states = []
            for ns, os in zip(flat_new, flat_old):
                ns_ov = get_ov_output(ns)
                os_ov = get_ov_output(os)
                masked_states.append(
                    OpenVINOKerasTensor(
                        ov_opset.select(mask_t_ov, ns_ov, os_ov).output(0)
                    )
                )
            states = tree.pack_sequence_as(new_states, masked_states)

            out_ov = get_ov_output(output_t)
            if last_output is not None:
                prev_ov = get_ov_output(last_output)
            else:
                prev_ov = ov_opset.broadcast(
                    ov_opset.constant(0, out_ov.get_element_type()).output(0),
                    ov_opset.shape_of(out_ov, Type.i32).output(0),
                ).output(0)

            last_output = OpenVINOKerasTensor(
                ov_opset.select(mask_t_ov, out_ov, prev_ov).output(0)
            )

            if zero_output_for_mask:
                zero = ov_opset.broadcast(
                    ov_opset.constant(0, out_ov.get_element_type()).output(0),
                    ov_opset.shape_of(out_ov, Type.i32).output(0),
                ).output(0)
                seq_out = OpenVINOKerasTensor(
                    ov_opset.select(mask_t_ov, out_ov, zero).output(0)
                )
            else:
                seq_out = last_output
        else:
            states = list(new_states)
            last_output = output_t
            seq_out = output_t

        if return_all_outputs:
            successive_outputs.append(seq_out)
        else:
            successive_outputs = [seq_out]

    # Stack outputs along time axis (axis=0, inputs are time-major here).
    flat_outputs = [tree.flatten(o) for o in successive_outputs]
    n_outs = len(flat_outputs[0])
    stacked = []
    unsq_ax = ov_opset.constant([0], dtype=Type.i32).output(0)
    for i in range(n_outs):
        parts = [
            ov_opset.unsqueeze(
                get_ov_output(flat_outputs[t][i]), unsq_ax
            ).output(0)
            for t in range(len(successive_outputs))
        ]
        stacked.append(
            OpenVINOKerasTensor(ov_opset.concat(parts, axis=0).output(0))
        )
    outputs = tree.pack_sequence_as(successive_outputs[0], stacked)

    if not time_major:
        outputs = tree.map_structure(swap_batch_timestep, outputs)

    return last_output, outputs, list(states)