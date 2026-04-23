def _cudnn_lstm(
    inputs,
    initial_state_h,
    initial_state_c,
    kernel,
    recurrent_kernel,
    bias,
    mask,
    time_major,
    go_backwards,
    return_sequences,
):
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
    # For init_h and init_c, cuDNN expects one more dim of num_layers before or
    # after batch dim for time major or batch major inputs respectively
    init_h = tf.expand_dims(initial_state_h, axis=seq_axis)
    init_c = tf.expand_dims(initial_state_c, axis=seq_axis)

    weights = tf.split(kernel, 4, axis=1)
    weights += tf.split(recurrent_kernel, 4, axis=1)
    # cuDNN has an extra set of bias for inputs, we disable them (setting to 0),
    # so that mathematically it is same as the canonical LSTM implementation.
    full_bias = tf.concat((tf.zeros_like(bias), bias), 0)

    if tf.sysconfig.get_build_info()["is_rocm_build"]:
        # ROCm MIOpen's weight sequence for LSTM is different from both
        # canonical and cuDNN format
        # MIOpen: [i, f, o, c] cuDNN/Canonical: [i, f, c, o]
        # i is input gate weights.
        # f is forget gate weights.
        # o is output gate weights.
        # c is cell gate weights.
        weights = [weights[x] for x in (0, 1, 3, 2, 4, 5, 7, 6)]
        # full_bias is a tensor of shape (8*n,)
        full_bias = tf.split(full_bias, 8, axis=0)
        full_bias = [full_bias[x] for x in (0, 1, 3, 2, 4, 5, 7, 6)]

    params = _standardize_cudnn_weights(
        weights=weights,
        biases=tf.split(full_bias, 8),
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
    outputs, h, c, _, _ = tf.raw_ops.CudnnRNNV3(
        input=inputs,
        input_h=init_h,
        input_c=init_c,
        params=params,
        is_training=True,
        rnn_mode="lstm",
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
    h = tf.squeeze(h, axis=seq_axis)
    c = tf.squeeze(c, axis=seq_axis)

    # In the case of variable length input, the cudnn kernel will fill zeros for
    # the output, whereas the default keras behavior is to bring over the
    # previous output for t-1, so that in the return_sequence=False case, user
    # can quickly get the final effect output instead just 0s at the last
    # timestep.  In order to mimic the default keras behavior, we copy the final
    # h state as the last_output, since it is numerically same as the output.
    if sequence_lengths is not None:
        last_output = h

    # Match CPU return format
    if not return_sequences:
        outputs = tf.expand_dims(last_output, axis=0 if time_major else 1)

    return (last_output, outputs, [h, c])