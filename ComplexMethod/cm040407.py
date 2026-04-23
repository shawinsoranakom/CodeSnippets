def nanquantile(x, q, axis=None, method="linear", keepdims=False):
    x = convert_to_tensor(x)
    q = convert_to_tensor(q, dtype=config.floatx())

    def _nanquantile_1d(v):
        valid = tf.boolean_mask(v, ~tf.math.is_nan(cast(v, config.floatx())))
        return tf.cond(
            tf.size(valid) > 0,
            lambda: quantile(valid, q, method=method, keepdims=False),
            lambda: tf.constant(float("nan"), dtype=x.dtype),
        )

    if axis is None:
        x_flat = tf.reshape(x, [-1])
        result = _nanquantile_1d(x_flat)

        if keepdims:
            new_shape = tf.concat(
                [tf.shape(result), tf.ones(tf.rank(x), dtype=tf.int32)], axis=0
            )
            result = tf.reshape(result, new_shape)

        return result

    if isinstance(axis, int):
        axis = [axis]
    elif isinstance(axis, tuple):
        axis = list(axis)

    ndims = x.shape.rank
    axis = [a if a >= 0 else a + ndims for a in axis]
    other_axes = [i for i in range(ndims) if i not in axis]

    perm = other_axes + axis
    x_t = tf.transpose(x, perm)

    shape = tf.shape(x_t)
    other_rank = len(other_axes)
    other_shape = shape[:other_rank]
    reduce_shape = shape[other_rank:]

    batch_size = tf.reduce_prod(other_shape)
    reduction_size = tf.reduce_prod(reduce_shape)
    x_flat = tf.reshape(x_t, [batch_size, reduction_size])

    q_shape = tf.shape(q)

    results = tf.map_fn(
        _nanquantile_1d,
        x_flat,
        fn_output_signature=tf.TensorSpec(shape=q_shape, dtype=x.dtype),
    )

    if tf.rank(q) > 0:
        results = tf.transpose(results)
        results = tf.reshape(results, tf.concat([q_shape, other_shape], axis=0))
    else:
        results = tf.reshape(results, other_shape)

    if keepdims:
        for ax in sorted(axis):
            results = tf.expand_dims(results, axis=ax + tf.rank(q))

    return results