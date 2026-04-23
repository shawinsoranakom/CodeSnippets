def ctc_decode(
    inputs,
    sequence_lengths,
    strategy="greedy",
    beam_width=100,
    top_paths=1,
    merge_repeated=True,
    mask_index=0,
):
    inputs = convert_to_tensor(inputs)
    input_shape = tf.shape(inputs)
    num_samples, num_steps = input_shape[0], input_shape[1]
    inputs = tf.transpose(inputs, (1, 0, 2))

    dtype = backend.result_type(inputs.dtype, "float32")
    inputs = tf.cast(inputs, dtype)

    sequence_lengths = convert_to_tensor(sequence_lengths, dtype="int32")
    if strategy == "greedy":
        (decoded, scores) = tf.nn.ctc_greedy_decoder(
            inputs=inputs,
            sequence_length=sequence_lengths,
            merge_repeated=merge_repeated,
            blank_index=mask_index,
        )
    elif strategy == "beam_search":
        # Move `mask_index` column to the last position since this is the
        # default for `tf.nn.ctc_beam_search_decoder`
        if mask_index is not None:
            inputs_before = inputs[..., :mask_index]
            inputs_mask = inputs[..., mask_index : mask_index + 1]
            inputs_after = inputs[..., mask_index + 1 :]
            inputs = tf.concat(
                [inputs_before, inputs_after, inputs_mask], axis=-1
            )
        (decoded, scores) = tf.nn.ctc_beam_search_decoder(
            inputs=inputs,
            sequence_length=sequence_lengths,
            beam_width=beam_width,
            top_paths=top_paths,
        )
    else:
        raise ValueError(
            f"Invalid strategy {strategy}. Supported values are "
            "'greedy' and 'beam_search'."
        )

    # Postprocess sparse tensor
    decoded_dense = []
    for st in decoded:
        st = tf.SparseTensor(st.indices, st.values, (num_samples, num_steps))
        decoded_dense.append(tf.sparse.to_dense(sp_input=st, default_value=-1))
    decoded_dense = tf.stack(decoded_dense, axis=0)
    decoded_dense = tf.cast(decoded_dense, "int32")

    # We need to recover the labels because we swapped the indices earlier
    if strategy == "beam_search" and mask_index is not None:
        if mask_index < 0:
            mask_index = mask_index + input_shape[-1]
        decoded_dense = tf.where(
            decoded_dense >= mask_index, decoded_dense + 1, decoded_dense
        )
    return decoded_dense, scores