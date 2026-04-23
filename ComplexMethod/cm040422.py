def one_hot(x, num_classes, axis=-1, dtype=None, sparse=False):
    x = convert_to_tensor(x, dtype="int64")
    if dtype is None:
        dtype = "float32"
    else:
        dtype = backend.standardize_dtype(dtype)
    if sparse:
        # We don't use `tf.sparse.bincount`, it doesn't handle negative indices
        # and only support rank 1 and 2 tensors (`one_hot` adds a dimension).
        if axis < 0:
            axis = axis + len(x.shape) + 1
        values_count = math.prod(x.shape)
        values = tf.reshape(x, (values_count,))
        # We deal with negative inputs by having zeros in the output although
        # it's useless. It makes shapes static.
        values = tf.cast(tf.greater_equal(values, 0), dtype=dtype)
        indices = [tf.range(dim) for dim in x.shape]
        indices = tf.meshgrid(*indices, indexing="ij")
        indices.insert(axis, tf.maximum(x, 0))  # Deal with negative indices
        indices = [tf.reshape(a, (values_count, 1)) for a in indices]
        indices = [tf.cast(a, tf.int64) for a in indices]
        indices = tf.concat(indices, axis=1)
        shape = list(x.shape)
        shape.insert(axis, num_classes)
        return tf.SparseTensor(indices, values, shape)
    on_value, off_value = (True, False) if dtype == "bool" else (None, None)
    return tf.one_hot(
        x,
        num_classes,
        on_value=on_value,
        off_value=off_value,
        axis=axis,
        dtype=dtype,
    )