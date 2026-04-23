def _interleave_with_b(a):
            a_shape = a.shape.as_list() if a.shape.rank is not None else None
            if isinstance(axis, int):
                b_shape_at_axis = b.shape[axis]
                num_elems_b_static = tf.get_static_value(
                    b_shape_at_axis
                    if b_shape_at_axis is not None
                    else tf.shape(b)[axis]
                )
            else:
                num_elems_b_static = None

            if (
                isinstance(axis, int)
                and a_shape is not None
                and num_elems_b_static is not None
                and all(
                    d is not None for i, d in enumerate(a_shape) if i != axis
                )
            ):
                new_shape = (
                    a_shape[:axis]
                    + [2 * num_elems_b_static]
                    + a_shape[axis + 1 :]
                )
            else:
                new_shape = tf.concat(
                    [
                        tf.shape(a)[:axis],
                        [2 * num_elems_b],
                        tf.shape(a)[axis + 1 :],
                    ],
                    axis=0,
                )
            return tf.reshape(
                # Work around lack of support for Tensor axes in
                # `tf.stack` by using `concat` and `expand_dims` instead.
                tf.concat(
                    [
                        tf.expand_dims(a, axis=axis + 1),
                        tf.expand_dims(b, axis=axis + 1),
                    ],
                    axis=axis + 1,
                ),
                new_shape,
            )