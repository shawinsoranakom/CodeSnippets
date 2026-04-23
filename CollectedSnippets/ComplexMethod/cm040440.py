def lstsq(a, b, rcond=None):
    a = convert_to_tensor(a)
    b = convert_to_tensor(b)
    if a.shape[0] != b.shape[0]:
        raise ValueError("Leading dimensions of input arrays must match")
    b_orig_ndim = b.ndim
    if b_orig_ndim == 1:
        b = b[:, None]
    if a.ndim != 2:
        raise TypeError(
            f"{a.ndim}-dimensional array given. Array must be two-dimensional"
        )
    if b.ndim != 2:
        raise TypeError(
            f"{b.ndim}-dimensional array given. "
            "Array must be one or two-dimensional"
        )
    m, n = a.shape
    dtype = a.dtype
    eps = tf.experimental.numpy.finfo(dtype).eps
    if a.shape == ():
        s = tf.zeros(0, dtype=a.dtype)
        x = tf.zeros((n, *b.shape[1:]), dtype=a.dtype)
    else:
        if rcond is None:
            rcond = eps * max(n, m)
        else:
            rcond = tf.where(rcond < 0, eps, rcond)
        u, s, vt = svd(a, full_matrices=False)
        mask = s >= tf.convert_to_tensor(rcond, dtype=s.dtype) * s[0]
        safe_s = tf.cast(tf.where(mask, s, 1), dtype=a.dtype)
        s_inv = tf.where(mask, 1 / safe_s, 0)[:, tf.newaxis]
        u_t_b = tf.matmul(tf.transpose(tf.math.conj(u)), b)
        x = tf.matmul(tf.transpose(tf.math.conj(vt)), s_inv * u_t_b)

    if b_orig_ndim == 1:
        x = tf.reshape(x, [-1])
    return x