def convert_to_tensor(x, dtype=None, sparse=None, ragged=None):
    if isinstance(x, tf.SparseTensor) and sparse is not None and not sparse:
        x = sparse_to_dense(x)
    if isinstance(x, tf.RaggedTensor) and ragged is not None and not ragged:
        x = x.to_tensor()
    if dtype is not None:
        dtype = standardize_dtype(dtype)
    if not tf.is_tensor(x):
        if dtype == "bool" or is_int_dtype(dtype):
            # TensorFlow conversion is stricter than other backends, it does not
            # allow ints for bools or floats for ints. We convert without dtype
            # and cast instead.
            x = tf.convert_to_tensor(x)
            return tf.cast(x, dtype)
        return tf.convert_to_tensor(x, dtype=dtype)
    elif dtype is not None and not standardize_dtype(x.dtype) == dtype:
        if isinstance(x, tf.SparseTensor):
            x_shape = x.shape
            x = tf.cast(x, dtype)
            x.set_shape(x_shape)
            return x
        return tf.cast(x, dtype=dtype)
    return x