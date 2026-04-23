def _rms_normalization(x, scale=None, axis=-1, epsilon=None):
    if epsilon is None:
        epsilon = backend.epsilon()
    original_dtype = backend.standardize_dtype(x.dtype)
    # Computes in at least float32 precision for stability in half precision
    # training.
    compute_dtype = backend.result_type(x.dtype, "float32")

    x = backend.convert_to_tensor(x, dtype=compute_dtype)
    if scale is not None:
        scale = backend.convert_to_tensor(scale, x.dtype)

    if isinstance(axis, (tuple, list)):
        axis = sorted(axis)
    if backend.backend() == "torch" and is_continuous_axis(axis):
        import torch.nn.functional as F

        if isinstance(axis, (tuple, list)):
            normalized_shape = tuple(x.shape[dim] for dim in axis)
        else:
            normalized_shape = (x.shape[axis],)
        outputs = F.rms_norm(x, normalized_shape, scale, epsilon)
    else:
        if len(x.shape) == 0:
            x = backend.numpy.expand_dims(x, axis=0)
        rrms = backend.math.rsqrt(
            backend.numpy.mean(
                backend.numpy.square(x), axis=axis, keepdims=True
            )
            + epsilon
        )
        outputs = backend.numpy.multiply(x, rrms)
        if scale is not None:
            outputs = backend.numpy.multiply(outputs, scale)
    return backend.cast(outputs, original_dtype)