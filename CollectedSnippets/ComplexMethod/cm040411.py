def squeeze(x, axis=None):
    x = convert_to_tensor(x)
    axis = to_tuple_or_list(axis)
    static_shape = x.shape.as_list()
    if axis is not None:
        for a in axis:
            if static_shape[a] != 1:
                raise ValueError(
                    f"Cannot squeeze axis={a}, because the dimension is not 1."
                )
        axis = sorted([canonicalize_axis(a, len(static_shape)) for a in axis])
    if isinstance(x, tf.SparseTensor):
        dynamic_shape = tf.shape(x)
        new_shape = []
        gather_indices = []
        for i, dim in enumerate(static_shape):
            if not (dim == 1 if axis is None else i in axis):
                new_shape.append(dim if dim is not None else dynamic_shape[i])
                gather_indices.append(i)
        new_indices = tf.gather(x.indices, gather_indices, axis=1)
        return tf.SparseTensor(new_indices, x.values, tuple(new_shape))
    return tf.squeeze(x, axis=axis)