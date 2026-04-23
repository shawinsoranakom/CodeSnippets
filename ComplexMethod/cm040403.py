def diagonal(x, offset=0, axis1=0, axis2=1):
    x = convert_to_tensor(x)
    x_rank = x.ndim
    if (
        offset == 0
        and (axis1 == x_rank - 2 or axis1 == -2)
        and (axis2 == x_rank - 1 or axis2 == -1)
    ):
        return tf.linalg.diag_part(x)

    x = moveaxis(x, (axis1, axis2), (-2, -1))
    x_shape = shape_op(x)

    def _zeros():
        return tf.zeros(tf.concat([x_shape[:-1], [0]], 0), dtype=x.dtype)

    if isinstance(x_shape[-1], int) and isinstance(x_shape[-2], int):
        if offset <= -1 * x_shape[-2] or offset >= x_shape[-1]:
            x = _zeros()
    else:
        x = tf.cond(
            tf.logical_or(
                tf.less_equal(offset, -1 * x_shape[-2]),
                tf.greater_equal(offset, x_shape[-1]),
            ),
            lambda: _zeros(),
            lambda: x,
        )
    return tf.linalg.diag_part(x, k=offset)