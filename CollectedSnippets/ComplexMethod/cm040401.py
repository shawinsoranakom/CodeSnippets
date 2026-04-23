def view(x, dtype=None):
    from keras.src import backend

    x = convert_to_tensor(x)
    old_dtype = tf.as_dtype(backend.standardize_dtype(x.dtype))
    new_dtype = tf.as_dtype(
        backend.standardize_dtype(dtype if dtype else x.dtype)
    )

    old_itemsize = old_dtype.size
    new_itemsize = new_dtype.size

    old_shape = list(shape_op(x))
    last_dim_size = old_shape[-1] if len(old_shape) > 0 else -1
    if (last_dim_size == -1 and old_itemsize != new_itemsize) or (
        last_dim_size * old_itemsize % new_itemsize != 0
    ):
        raise ValueError(
            f"Cannot view array of shape {x.shape} and dtype {old_dtype} "
            f"as dtype {new_dtype} because the total number of bytes "
            f"is not divisible by the new itemsize."
        )

    if old_itemsize == new_itemsize:
        return tf.bitcast(x, type=new_dtype)
    elif old_itemsize > new_itemsize:
        ratio = old_itemsize // new_itemsize
        new_shape = list(shape_op(x))
        new_shape[-1] *= ratio
        flat_tensor = tf.reshape(x, [-1])
        cast_tensor = tf.bitcast(flat_tensor, type=new_dtype)
        return tf.reshape(cast_tensor, new_shape)
    else:
        ratio = new_itemsize // old_itemsize
        if isinstance(last_dim_size, int) and last_dim_size % ratio != 0:
            raise ValueError(
                f"Cannot view dtype. Last dimension size ({last_dim_size}) "
                f"must be divisible by the ratio of new/old item sizes "
                f"({ratio})."
            )
        intermediate_shape = old_shape[:-1] + [last_dim_size // ratio, ratio]
        reshaped_tensor = tf.reshape(x, intermediate_shape)
        return tf.bitcast(reshaped_tensor, new_dtype)