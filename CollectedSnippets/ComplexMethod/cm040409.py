def take_along_axis(x, indices, axis=None):
    from keras.src.ops import operation_utils

    x = convert_to_tensor(x)
    indices = convert_to_tensor(indices, "int64")
    if axis is None:
        if indices.ndim != 1:
            raise ValueError(
                "`indices` must be 1D if axis=None. "
                f"Received: indices.shape={indices.shape}"
            )
        return take_along_axis(tf.reshape(x, [-1]), indices, 0)

    # Compute the static output shape as later on, all shapes manipulations
    # use dynamic shapes.
    static_output_shape = operation_utils.compute_take_along_axis_output_shape(
        x.shape, indices.shape, axis
    )
    rank = x.ndim
    static_axis = axis
    axis = axis + rank if axis < 0 else axis

    if axis >= rank:
        raise ValueError(f"Invalid axis: {static_axis} for input rank: {rank}")

    x_original_shape = shape_op(x)
    indices_original_shape = shape_op(indices)

    # Broadcast the static shapes first, but not for the `axis` dimension.
    x_static_shape = list(x.shape)
    indices_static_shape = list(indices.shape)
    x_static_shape[axis] = 1
    indices_static_shape[axis] = 1
    broadcast_shape = operation_utils.broadcast_shapes(
        x_static_shape, indices_static_shape
    )

    if None in broadcast_shape:
        # Dynamic broadcast case. Note that `tf.broadcast_dynamic_shape` is
        # not always XLA compilable with dynamic dimensions.
        # We replace `None`s with the dynamic dimensions.
        # `maximum` is the correct formula only when shapes are broadcastable,
        # we rely on the broacast itself to fail in the incorrect case rather
        # than make some expensive dynamic checks here.
        broadcast_shape = [
            tf.maximum(x_original_shape[i], indices_original_shape[i])
            if dim is None
            else dim
            for i, dim in enumerate(broadcast_shape)
        ]

    x_shape = list(broadcast_shape)
    x_shape[axis] = x_original_shape[axis]
    indices_shape = list(broadcast_shape)
    indices_shape[axis] = indices_original_shape[axis]
    x = tf.broadcast_to(x, x_shape)
    indices = tf.broadcast_to(indices, indices_shape)

    # Correct the indices using "fill" mode which is the same as in jax
    indices = tf.where(
        indices < 0,
        indices + tf.cast(x_shape[static_axis], dtype=indices.dtype),
        indices,
    )

    x = swapaxes(x, static_axis, -1)
    indices = swapaxes(indices, static_axis, -1)

    x_shape = tf.shape(x)
    x = tf.reshape(x, [-1, x_shape[-1]])
    indices_shape = tf.shape(indices)
    indices = tf.reshape(indices, [-1, indices_shape[-1]])

    result = tf.gather(x, indices, batch_dims=1)
    result = tf.reshape(result, indices_shape)
    result = swapaxes(result, static_axis, -1)
    result.set_shape(static_output_shape)
    return result