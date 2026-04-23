def batch_dot(x, y, axes=None):
    """DEPRECATED."""
    x_shape = x.shape
    y_shape = y.shape

    x_ndim = len(x_shape)
    y_ndim = len(y_shape)

    if x_ndim < 2 or y_ndim < 2:
        raise ValueError(
            "Cannot do batch_dot on inputs "
            "with rank < 2. "
            f"Received inputs with tf.shapes {x_shape} and {y_shape}."
        )

    x_batch_size = x_shape[0]
    y_batch_size = y_shape[0]

    if x_batch_size is not None and y_batch_size is not None:
        if x_batch_size != y_batch_size:
            raise ValueError(
                "Cannot do batch_dot on inputs "
                "with different batch sizes. "
                "Received inputs with tf.shapes "
                f"{x_shape} and {y_shape}."
            )
    if isinstance(axes, int):
        axes = [axes, axes]

    if axes is None:
        if y_ndim == 2:
            axes = [x_ndim - 1, y_ndim - 1]
        else:
            axes = [x_ndim - 1, y_ndim - 2]

    if py_any(isinstance(a, (list, tuple)) for a in axes):
        raise ValueError(
            "Multiple target dimensions are not supported. "
            "Expected: None, int, (int, int), "
            f"Provided: {axes}"
        )

    # if tuple, convert to list.
    axes = list(axes)

    # convert negative indices.
    if axes[0] < 0:
        axes[0] += x_ndim
    if axes[1] < 0:
        axes[1] += y_ndim

    # sanity checks
    if 0 in axes:
        raise ValueError(
            "Cannot perform batch_dot over axis 0. "
            "If your inputs are not batched, "
            "add a dummy batch dimension to your "
            "inputs using K.expand_dims(x, 0)"
        )
    a0, a1 = axes
    d1 = x_shape[a0]
    d2 = y_shape[a1]

    if d1 is not None and d2 is not None and d1 != d2:
        raise ValueError(
            "Cannot do batch_dot on inputs with tf.shapes "
            f"{x_shape} and {y_shape} with axes={axes}. "
            "x.shape[%d] != y.shape[%d] (%d != %d)."
            % (axes[0], axes[1], d1, d2)
        )

    # backup ndims. Need them later.
    orig_x_ndim = x_ndim
    orig_y_ndim = y_ndim

    # if rank is 2, expand to 3.
    if x_ndim == 2:
        x = tf.expand_dims(x, 1)
        a0 += 1
        x_ndim += 1
    if y_ndim == 2:
        y = tf.expand_dims(y, 2)
        y_ndim += 1

    # bring x's dimension to be reduced to last axis.
    if a0 != x_ndim - 1:
        pattern = list(range(x_ndim))
        for i in range(a0, x_ndim - 1):
            pattern[i] = pattern[i + 1]
        pattern[-1] = a0
        x = tf.transpose(x, pattern)

    # bring y's dimension to be reduced to axis 1.
    if a1 != 1:
        pattern = list(range(y_ndim))
        for i in range(a1, 1, -1):
            pattern[i] = pattern[i - 1]
        pattern[1] = a1
        y = tf.transpose(y, pattern)

    # normalize both inputs to rank 3.
    if x_ndim > 3:
        # squash middle dimensions of x.
        x_shape = tf.shape(x)
        x_mid_dims = x_shape[1:-1]
        x_squashed_shape = tf.stack([x_shape[0], -1, x_shape[-1]])
        x = tf.reshape(x, x_squashed_shape)
        x_squashed = True
    else:
        x_squashed = False

    if y_ndim > 3:
        # squash trailing dimensions of y.
        y_shape = tf.shape(y)
        y_trail_dims = y_shape[2:]
        y_squashed_shape = tf.stack([y_shape[0], y_shape[1], -1])
        y = tf.reshape(y, y_squashed_shape)
        y_squashed = True
    else:
        y_squashed = False

    result = tf.matmul(x, y)

    # if inputs were squashed, we have to reshape the matmul output.
    output_shape = tf.shape(result)
    do_reshape = False

    if x_squashed:
        output_shape = tf.concat(
            [output_shape[:1], x_mid_dims, output_shape[-1:]], 0
        )
        do_reshape = True

    if y_squashed:
        output_shape = tf.concat([output_shape[:-1], y_trail_dims], 0)
        do_reshape = True

    if do_reshape:
        result = tf.reshape(result, output_shape)

    # if the inputs were originally rank 2, we remove the added 1 dim.
    if orig_x_ndim == 2:
        result = tf.squeeze(result, 1)
    elif orig_y_ndim == 2:
        result = tf.squeeze(result, -1)

    return result