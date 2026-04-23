def bincount(x, weights=None, minlength=0, sparse=False):
    x = convert_to_tensor(x)
    dtypes_to_resolve = [x.dtype]
    if standardize_dtype(x.dtype) not in ["int32", "int64"]:
        x = tf.cast(x, tf.int32)
    if weights is not None:
        weights = convert_to_tensor(weights)
        dtypes_to_resolve.append(weights.dtype)
        dtype = dtypes.result_type(*dtypes_to_resolve)
        if standardize_dtype(weights.dtype) not in [
            "int32",
            "int64",
            "float32",
            "float64",
        ]:
            if "int" in standardize_dtype(weights.dtype):
                weights = tf.cast(weights, tf.int32)
            else:
                weights = tf.cast(weights, tf.float32)
    else:
        dtype = "int32"
    if sparse or isinstance(x, tf.SparseTensor):
        output = tf.sparse.bincount(
            x,
            weights=weights,
            minlength=minlength,
            axis=-1,
        )
        actual_length = output.shape[-1]
        if actual_length is None:
            actual_length = tf.shape(output)[-1]
        output = cast(output, dtype)
        if x.shape.rank == 1:
            output_shape = (actual_length,)
        else:
            batch_size = output.shape[0]
            if batch_size is None:
                batch_size = tf.shape(output)[0]
            output_shape = (batch_size, actual_length)
        return tf.SparseTensor(
            indices=output.indices,
            values=output.values,
            dense_shape=output_shape,
        )
    return tf.cast(
        tf.math.bincount(x, weights=weights, minlength=minlength, axis=-1),
        dtype,
    )