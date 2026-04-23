def _layer_normalization(
    x, gamma=None, beta=None, axis=-1, epsilon=None, rms_scaling=False
):
    if epsilon is None:
        epsilon = backend.epsilon()
    original_dtype = backend.standardize_dtype(x.dtype)
    # Computes in at least float32 precision for stability in half precision
    # training.
    compute_dtype = backend.result_type(x.dtype, "float32")

    x = backend.convert_to_tensor(x, dtype=compute_dtype)
    if gamma is not None:
        gamma = backend.convert_to_tensor(gamma, x.dtype)
    if beta is not None:
        beta = backend.convert_to_tensor(beta, x.dtype)

    # Compute the axes along which to reduce the mean / variance
    input_shape = x.shape
    ndims = len(input_shape)

    # Broadcasting only necessary for norm when the axis is not just
    # the last dimension
    broadcast_shape = [1] * ndims
    if isinstance(axis, int):
        axis = [axis]
    axis = sorted(axis)
    for dim in axis:
        broadcast_shape[dim] = input_shape[dim]

    def _broadcast(v):
        if v is not None and len(v.shape) != ndims and axis != [ndims - 1]:
            return backend.numpy.reshape(v, broadcast_shape)
        return v

    if rms_scaling:
        variance = backend.numpy.var(x, axis=axis, keepdims=True)
        inv = backend.math.rsqrt(variance + epsilon)
        outputs = outputs = x * inv
        if gamma is not None:
            outputs = outputs * backend.cast(_broadcast(gamma), x.dtype)
    elif backend.config.backend() == "torch" and is_continuous_axis(axis):
        # when using torch backend,use kernel to improve performance
        import torch.nn.functional as F

        normalized_shape = tuple(input_shape[dim] for dim in axis)
        outputs = F.layer_norm(x, normalized_shape, gamma, beta, epsilon)
    else:
        # Calculate the mean & variance along self.axis (layer activations).
        mean, variance = moments(x, axes=axis, keepdims=True)
        gamma, beta = _broadcast(gamma), _broadcast(beta)
        inv = backend.math.rsqrt(variance + epsilon)
        if gamma is not None:
            inv = inv * gamma

        res = -mean * inv
        if beta is not None:
            res = res + beta

        outputs = x * inv + res
    return backend.cast(outputs, original_dtype)