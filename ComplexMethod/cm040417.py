def _cudnn_gru(
    inputs,
    initial_state,
    kernel,
    recurrent_kernel,
    bias,
    mask,
    time_major,
    go_backwards,
    return_sequences,
):
    """GRU with cuDNN implementation which is only available for GPU."""
    if mask is not None:
        _assert_valid_mask(mask)
        sequence_lengths = _compute_sequence_length_from_mask(mask, time_major)
    else:
        if time_major:
            batch_dim = tf.shape(inputs)[1]
            max_sequence_length = tf.shape(inputs)[0]
        else:
            batch_dim = tf.shape(inputs)[0]
            max_sequence_length = tf.shape(inputs)[1]
        sequence_lengths = tf.fill([batch_dim], max_sequence_length)

    if not time_major and sequence_lengths is None:
        inputs = tf.transpose(inputs, perm=(1, 0, 2))
        seq_axis, batch_axis = (0, 1)
    else:
        seq_axis, batch_axis = (0, 1) if time_major else (1, 0)

    # For init_h, cuDNN expects one more dim of num_layers before or after batch
    # dim for time major or batch major inputs respectively
    init_h = tf.expand_dims(initial_state, axis=seq_axis)

    weights = tf.split(kernel, 3, axis=1)
    weights += tf.split(recurrent_kernel, 3, axis=1)
    # Note that the bias was initialized as shape (2, 3 * units), flatten it to
    # (6 * units)
    bias = tf.split(tf.reshape(bias, [-1]), 6)

    if tf.sysconfig.get_build_info()["is_cuda_build"]:
        # Note that the gate order for cuDNN is different from the canonical
        # format.  canonical format is [z, r, h], whereas cuDNN is [r, z, h].
        # The swap need to be done for kernel, recurrent_kernel, input_bias,
        # recurrent_bias.
        # z is update gate weights.
        # r is reset gate weights.
        # h is output gate weights.
        weights[0], weights[1] = weights[1], weights[0]
        weights[3], weights[4] = weights[4], weights[3]
        bias[0], bias[1] = bias[1], bias[0]
        bias[3], bias[4] = bias[4], bias[3]

    params = _standardize_cudnn_weights(
        weights=weights,
        biases=bias,
        shape=tf.constant([-1]),
        transpose_weights=True,
    )

    if go_backwards:
        # Three reversals are required. E.g.,
        # normal input = [1, 2, 3, 0, 0]  # where 0 need to be masked
        # reversed_input_to_cudnn = [3, 2, 1, 0, 0]
        # output_from_cudnn = [6, 5, 4, 0, 0]
        # expected_output = [0, 0, 6, 5 ,4]
        inputs = tf.reverse_sequence(
            inputs,
            sequence_lengths,
            seq_axis=seq_axis,
            batch_axis=batch_axis,
        )
    outputs, h, _, _, _ = tf.raw_ops.CudnnRNNV3(
        input=inputs,
        input_h=init_h,
        input_c=0,
        params=params,
        is_training=True,
        rnn_mode="gru",
        sequence_lengths=sequence_lengths,
        time_major=time_major,
    )
    if go_backwards:
        outputs = tf.reverse_sequence(
            outputs,
            sequence_lengths,
            seq_axis=seq_axis,
            batch_axis=batch_axis,
        )
        outputs = tf.reverse(outputs, axis=[seq_axis])

    last_output = outputs[-1]
    if not time_major and sequence_lengths is None and return_sequences:
        outputs = tf.transpose(outputs, perm=[1, 0, 2])
    state = tf.squeeze(h, axis=seq_axis)

    # In the case of variable length input, the cudnn kernel will fill zeros for
    # the output, whereas the default keras behavior is to bring over the
    # previous output for t-1, so that in the return_sequence=False case, user
    # can quickly get the final effect output instead just 0s at the last
    # timestep.  In order to mimic the default keras behavior, we copy the final
    # h state as the last_output, since it is numerically same as the output.
    if sequence_lengths is not None:
        last_output = state

    # Match CPU return format
    if not return_sequences:
        outputs = tf.expand_dims(last_output, axis=0 if time_major else 1)

    return (
        last_output,
        outputs,
        [state],
    )