def tf_encode_categorical_inputs(
    inputs,
    output_mode,
    depth,
    dtype="float32",
    sparse=False,
    count_weights=None,
    idf_weights=None,
):
    """Encodes categorical inputs according to output_mode.

    Faster method that relies on bincount.
    """

    if output_mode == "int":
        return tf.identity(tf.cast(inputs, dtype))

    original_shape = inputs.shape
    # In all cases, we should uprank scalar input to a single sample.
    if inputs.shape.rank == 0:
        inputs = expand_dims(inputs, -1)
    # One hot will uprank only if the final output dimension is not already 1.
    if output_mode == "one_hot":
        if inputs.shape[-1] != 1:
            inputs = expand_dims(inputs, -1)

    if inputs.shape.rank > 2:
        raise ValueError(
            "When output_mode is not `'int'`, maximum supported output rank "
            f"is 2. Received output_mode {output_mode} and input shape "
            f"{original_shape}, "
            f"which would result in output rank {inputs.shape.rank}."
        )

    binary_output = output_mode in ("multi_hot", "one_hot")
    if sparse:
        bincounts = sparse_bincount(
            inputs, depth, binary_output, dtype, count_weights
        )
    else:
        bincounts = dense_bincount(
            inputs, depth, binary_output, dtype, count_weights
        )

    bincounts = tf.cast(bincounts, dtype)
    if output_mode != "tf_idf":
        return bincounts

    if idf_weights is None:
        raise ValueError(
            "When output mode is `'tf_idf'`, idf_weights must be provided. "
            f"Received: output_mode={output_mode} and idf_weights={idf_weights}"
        )

    if sparse:
        value_weights = tf.gather(idf_weights, bincounts.indices[:, -1])
        return tf.SparseTensor(
            bincounts.indices,
            value_weights * bincounts.values,
            bincounts.dense_shape,
        )
    else:
        return tf.multiply(bincounts, idf_weights)