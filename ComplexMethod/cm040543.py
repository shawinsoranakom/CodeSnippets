def shape_equal(shape1, shape2, axis=None, allow_none=True):
    """Check if two shapes are equal.

    Args:
        shape1: A list or tuple of integers for first shape to be compared.
        shape2: A list or tuple of integers for second shape to be compared.
        axis: An integer, list, or tuple of integers (optional):
            Axes to ignore during comparison. Defaults to `None`.
        allow_none (bool, optional): If `True`, allows `None` in a shape
            to match any value in the corresponding position of the other shape.
            Defaults to `True`.

    Returns:
        bool: `True` if shapes are considered equal based on the criteria,
        `False` otherwise.

    Examples:

    >>> shape_equal((32, 64, 128), (32, 64, 128))
    True
    >>> shape_equal((32, 64, 128), (32, 64, 127))
    False
    >>> shape_equal((32, 64, None), (32, 64, 128), allow_none=True)
    True
    >>> shape_equal((32, 64, None), (32, 64, 128), allow_none=False)
    False
    >>> shape_equal((32, 64, 128), (32, 63, 128), axis=1)
    True
    >>> shape_equal((32, 64, 128), (32, 63, 127), axis=(1, 2))
    True
    >>> shape_equal((32, 64, 128), (32, 63, 127), axis=[1,2])
    True
    >>> shape_equal((32, 64), (32, 64, 128))
    False
    """
    if len(shape1) != len(shape2):
        return False

    shape1 = list(shape1)
    shape2 = list(shape2)

    if axis is not None:
        if isinstance(axis, int):
            axis = [axis]
        for ax in axis:
            shape1[ax] = -1
            shape2[ax] = -1

    if allow_none:
        for i in range(len(shape1)):
            if shape1[i] is None:
                shape1[i] = shape2[i]
            if shape2[i] is None:
                shape2[i] = shape1[i]

    return shape1 == shape2