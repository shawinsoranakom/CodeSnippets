def mean(x, axis=None, keepdims=False):
    if isinstance(x, tf.IndexedSlices):
        if axis is None:
            # Reduce against all axes, result is a single value and dense.
            # The denominator has to account for `dense_shape`.
            sum = tf.reduce_sum(x.values, keepdims=keepdims)
            return sum / tf.cast(tf.reduce_prod(x.dense_shape), dtype=sum.dtype)

        axis = to_tuple_or_list(axis)
        if not axis:
            # Empty axis tuple, this is a no-op
            return x

        dense_shape = tf.convert_to_tensor(x.dense_shape)
        rank = tf.shape(dense_shape)[0]
        # Normalize axis: convert negative values and sort
        axis = [canonicalize_axis(a, rank) for a in axis]
        axis.sort()

        if axis == [0]:
            # Reduce against `axis=0` only, result is dense.
            # The denominator has to account for `dense_shape[0]`.
            sum = tf.reduce_sum(x.values, axis=0, keepdims=keepdims)
            return sum / tf.cast(dense_shape[0], dtype=sum.dtype)
        elif axis[0] == 0:
            # Reduce against axis 0 and other axes, result is dense.
            # We do `axis=0` separately first. The denominator has to account
            # for `dense_shape[0]`.
            # We use `keepdims=True` in `reduce_sum`` so that we can leave the
            # 0 in axis and do `reduce_mean` with `keepdims` to apply it for all
            # axes.
            sum = tf.reduce_sum(x.values, axis=0, keepdims=True)
            axis_0_mean = sum / tf.cast(dense_shape[0], dtype=sum.dtype)
            return tf.reduce_mean(axis_0_mean, axis=axis, keepdims=keepdims)
        elif keepdims:
            # With `keepdims=True`, result is an `IndexedSlices` with the same
            # indices since axis 0 is not touched. The only thing to do is to
            # correct `dense_shape` to account for dimensions that became 1.
            new_values = tf.reduce_mean(x.values, axis=axis, keepdims=True)
            new_dense_shape = tf.concat(
                [dense_shape[0:1], new_values.shape[1:]], axis=0
            )
            return tf.IndexedSlices(new_values, x.indices, new_dense_shape)
        elif rank == len(axis) + 1:
            # `keepdims=False` and reducing against all axes except 0, result is
            # a 1D tensor, which cannot be `IndexedSlices`. We have to scatter
            # the computed means to construct the correct dense tensor.
            return tf.scatter_nd(
                tf.expand_dims(x.indices, axis=1),
                tf.reduce_mean(x.values, axis=axis),
                [dense_shape[0]],
            )
        else:
            # `keepdims=False`, not reducing against axis 0 and there is at
            # least one other axis we are not reducing against. We simply need
            # to fix `dense_shape` to remove dimensions that were reduced.
            gather_indices = [i for i in range(rank) if i not in axis]
            return tf.IndexedSlices(
                tf.reduce_mean(x.values, axis=axis),
                x.indices,
                tf.gather(x.dense_shape, gather_indices, axis=0),
            )
    x = convert_to_tensor(x)
    ori_dtype = standardize_dtype(x.dtype)
    compute_dtype = dtypes.result_type(x.dtype, "float32")
    # `tf.reduce_mean` does not handle low precision (e.g., float16) overflow
    # correctly, so we compute with float32 and cast back to the original type.
    if "int" in ori_dtype or ori_dtype == "bool":
        result_dtype = compute_dtype
    else:
        result_dtype = ori_dtype
    output = tf.reduce_mean(
        tf.cast(x, compute_dtype), axis=axis, keepdims=keepdims
    )
    return tf.cast(output, result_dtype)