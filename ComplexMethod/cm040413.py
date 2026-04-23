def unique(
    x,
    sorted=True,
    return_inverse=False,
    return_counts=False,
    axis=None,
    size=None,
    fill_value=None,
):
    x = tf.convert_to_tensor(x)
    is_flatten = axis is None
    original_shape = tf.shape(x)

    if is_flatten:
        x = tf.reshape(x, [-1])
        dim = 0
        y, inverse, counts = tf.unique_with_counts(x)

    else:
        ndim = x.shape.rank
        dim = axis + ndim if axis < 0 else axis
        axis_to_use = tf.constant([dim], dtype=tf.int32)
        y, inverse, counts = tf.raw_ops.UniqueWithCountsV2(
            x=x, axis=axis_to_use, out_idx=tf.int32
        )

    if sorted:
        num_unique = tf.shape(y)[dim]
        if is_flatten or y.shape.rank == 1:
            sort_order = tf.argsort(y)
        else:
            # Multi-D lexicographical sort
            perm = list(range(y.shape.rank))
            perm[0], perm[dim] = perm[dim], perm[0]
            y_transposed = tf.transpose(y, perm)
            y_2d = tf.reshape(y_transposed, [num_unique, -1])
            num_cols = tf.shape(y_2d)[1]

            sort_order = tf.range(num_unique, dtype=tf.int32)

            def body(i, current_indices):
                col = tf.gather(y_2d[:, i], current_indices)
                perm_sort = tf.argsort(col, stable=True)
                return i - 1, tf.gather(current_indices, perm_sort)

            def cond(i, current_indices):
                return i >= 0

            _, sort_order = tf.while_loop(
                cond, body, [num_cols - 1, sort_order], parallel_iterations=1
            )

        y = tf.gather(y, sort_order, axis=dim)
        if return_counts:
            counts = tf.gather(counts, sort_order)
        if return_inverse:
            # Must invert permutation to map inverse indices correctly
            inv_perm = tf.math.invert_permutation(sort_order)
            inverse = tf.gather(inv_perm, inverse)

    # Static size padding/truncation (branchless logic for graph mode safety)
    if size is not None:
        values_count = tf.shape(y)[dim]

        # 1. Truncate using gather
        truncate_size = tf.minimum(values_count, size)
        y = tf.gather(y, tf.range(truncate_size), axis=dim)
        if return_counts:
            counts = tf.gather(counts, tf.range(truncate_size))

        # 2. Pad using tf.pad (pad_amount = 0 makes it a no-op)
        pad_amount = tf.maximum(0, size - values_count)
        paddings = tf.zeros([tf.rank(y), 2], dtype=tf.int32)
        paddings = tf.tensor_scatter_nd_update(
            paddings, [[dim, 1]], [pad_amount]
        )

        fill = tf.cast(0 if fill_value is None else fill_value, y.dtype)
        y = tf.pad(y, paddings, constant_values=fill)

        if return_counts:
            counts = tf.pad(counts, [[0, pad_amount]], constant_values=0)

        # 3. Enforce static shape for JAX/XLA compatibility
        static_shape = y.shape.as_list()
        static_shape[dim] = size
        y.set_shape(static_shape)
        if return_counts:
            counts.set_shape([size])

    if return_inverse and is_flatten:
        inverse = tf.reshape(inverse, original_shape)

    results = [y]
    if return_inverse:
        results.append(inverse)
    if return_counts:
        results.append(counts)

    return tuple(results) if len(results) > 1 else results[0]