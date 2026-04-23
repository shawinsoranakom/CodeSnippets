def relu(x, alpha=0.0, max_value=None, threshold=0.0):
    """DEPRECATED."""
    # While x can be a tensor or variable, we also see cases where
    # numpy arrays, lists, tuples are passed as well.
    # lists, tuples do not have 'dtype' attribute.
    dtype = getattr(x, "dtype", backend.floatx())
    if alpha != 0.0:
        if max_value is None and threshold == 0:
            return tf.nn.leaky_relu(x, alpha=alpha)

        if threshold != 0:
            negative_part = tf.nn.relu(-x + threshold)
        else:
            negative_part = tf.nn.relu(-x)
    else:
        negative_part = 1

    clip_max = max_value is not None

    if threshold != 0:
        # computes x for x > threshold else 0
        x = x * tf.cast(tf.greater(x, threshold), dtype=dtype)
    elif max_value == 6:
        # if no threshold, then can use nn.relu6 native TF op for performance
        x = tf.nn.relu6(x)
        clip_max = False
    else:
        x = tf.nn.relu(x)

    if clip_max:
        max_value = tf.convert_to_tensor(max_value, dtype=x.dtype)
        zero = tf.convert_to_tensor(0, dtype=x.dtype)
        x = tf.clip_by_value(x, zero, max_value)

    if alpha != 0.0:
        alpha = tf.convert_to_tensor(alpha, dtype=x.dtype)
        x -= alpha * negative_part
    return x