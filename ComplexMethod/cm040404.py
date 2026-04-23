def dstack(xs):
    xs = [convert_to_tensor(x) for x in xs]
    if len(xs) > 1:
        unique_dtypes = {x.dtype for x in xs}
        if len(unique_dtypes) > 1:
            dtype = dtypes.result_type(*[x.dtype for x in xs])
            xs = [cast(x, dtype) for x in xs]
    xs_reshaped = []
    for x in xs:
        shape = x.shape
        if len(shape) == 0:
            x = tf.reshape(x, (1, 1, 1))
        elif len(shape) == 1:
            x = tf.expand_dims(x, axis=0)
            x = tf.expand_dims(x, axis=2)
        elif len(shape) == 2:
            x = tf.expand_dims(x, axis=2)
        xs_reshaped.append(x)
    return tf.concat(xs_reshaped, axis=2)