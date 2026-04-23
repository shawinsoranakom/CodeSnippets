def softmax(x, axis=-1):
    """Softmax activation function.

    The elements of the output vector lie within the range `(0, 1)`, and their
    total sum is exactly 1 (excluding the floating point rounding error).

    Each vector is processed independently. The `axis` argument specifies the
    axis along which the function is applied within the input.

    It is defined as:
    `f(x) = exp(x) / sum(exp(x))`

    Args:
        x: Input tensor.
        axis: Integer, axis along which the softmax is applied.

    Returns:
        A tensor with the same shape as `x`.

    Example:

    >>> x = np.array([-1., 0., 1.])
    >>> x_softmax = keras.ops.softmax(x)
    >>> print(x_softmax)
    array([0.09003057, 0.24472847, 0.66524096], shape=(3,), dtype=float64)

    """
    # Don't use `backend.shape` since TensorFlow returns
    # symbolic tensors for unknown shape which can trigger
    # an error in TensorFlow graph execution.
    if isinstance(axis, int) and x.shape[axis] == 1:
        warnings.warn(
            f"You are using a softmax over axis {axis} "
            f"of a tensor of shape {x.shape}. This axis "
            "has size 1. The softmax operation will always return "
            "the value 1, which is likely not what you intended. "
            "Did you mean to use a sigmoid instead?"
        )
    if any_symbolic_tensors((x,)):
        return Softmax(axis).symbolic_call(x)
    if isinstance(axis, tuple):
        axis_to_keep = [v for v in range(len(x.shape)) if v not in axis]

        x_transposed = backend.numpy.transpose(x, axes=(*axis_to_keep, *axis))
        x_reshaped = backend.numpy.reshape(
            x_transposed, (*[x.shape[v] for v in axis_to_keep], -1)
        )

        x = backend.nn.softmax(x_reshaped, axis=-1)

        x = backend.numpy.reshape(x, x_transposed.shape)
        combined = [*axis_to_keep, *axis]
        x = backend.numpy.transpose(
            x,
            axes=sorted(range(len(combined)), key=combined.__getitem__),
        )
        return x
    else:
        return backend.nn.softmax(x, axis=axis)