def _move_and_flatten_axes(axis, x_ndim, *tensors):
    """Transpose reduction axes to the end and flatten them into one dim.

    Returns (flattened_tensors..., norm_axis) where norm_axis is the
    normalised axis list (or None when axis was None).
    """
    if axis is None:
        flat_const = ov_opset.constant([-1], Type.i64).output(0)
        flattened = tuple(
            ov_opset.reshape(t, flat_const, False).output(0) for t in tensors
        )
        return flattened + (None,)

    if isinstance(axis, int):
        axis = [axis]
    axis = [a % x_ndim for a in axis]
    other_dims = sorted(set(range(x_ndim)).difference(axis))
    perm = ov_opset.constant(other_dims + list(axis), Type.i32).output(0)
    transposed = tuple(ov_opset.transpose(t, perm).output(0) for t in tensors)

    x_shape = ov_opset.shape_of(tensors[0], Type.i64).output(0)
    if other_dims:
        other_shape = ov_opset.gather(
            x_shape,
            ov_opset.constant(other_dims, Type.i32).output(0),
            ov_opset.constant(0, Type.i32).output(0),
        ).output(0)
        flat_shape = ov_opset.concat(
            [other_shape, ov_opset.constant([-1], Type.i64).output(0)],
            axis=0,
        ).output(0)
    else:
        flat_shape = ov_opset.constant([-1], Type.i64).output(0)

    flattened = tuple(
        ov_opset.reshape(t, flat_shape, False).output(0) for t in transposed
    )
    return flattened + (axis,)