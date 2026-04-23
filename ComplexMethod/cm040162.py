def concatenate(tensors, axis=-1):
    """DEPRECATED."""
    if axis < 0:
        rank = ndim(tensors[0])
        if rank:
            axis %= rank
        else:
            axis = 0

    if py_all(is_sparse(x) for x in tensors):
        return tf.compat.v1.sparse_concat(axis, tensors)
    elif py_all(isinstance(x, tf.RaggedTensor) for x in tensors):
        return tf.concat(tensors, axis)
    else:
        return tf.concat([to_dense(x) for x in tensors], axis)