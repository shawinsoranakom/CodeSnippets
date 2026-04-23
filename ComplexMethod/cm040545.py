def histogram(x, bins=10, range=None):
    """Computes a histogram of the data tensor `x`.

    Args:
        x: Input tensor.
        bins: An integer representing the number of histogram bins.
            Defaults to 10.
        range: A tuple representing the lower and upper range of the bins.
            If not specified, it will use the min and max of `x`.

    Returns:
        A tuple containing:
        - A tensor representing the counts of elements in each bin.
        - A tensor representing the bin edges.

    Example:
    >>> input_tensor = np.random.rand(8)
    >>> keras.ops.histogram(input_tensor)
    (array([1, 1, 1, 0, 0, 1, 2, 1, 0, 1], dtype=int32),
    array([0.0189519 , 0.10294958, 0.18694726, 0.27094494, 0.35494262,
        0.43894029, 0.52293797, 0.60693565, 0.69093333, 0.77493101,
        0.85892869]))
    """
    if not isinstance(bins, int):
        raise TypeError(
            f"Argument `bins` must be of type `int`. Received: bins={bins}"
        )
    if bins < 0:
        raise ValueError(
            "Argument `bins` should be a non-negative integer. "
            f"Received: bins={bins}"
        )

    if range:
        if len(range) < 2 or not isinstance(range, tuple):
            raise ValueError(
                "Argument `range` must be a tuple of two elements. "
                f"Received: range={range}"
            )

        if range[1] < range[0]:
            raise ValueError(
                "The second element of `range` must be greater than the first. "
                f"Received: range={range}"
            )

    if any_symbolic_tensors((x,)):
        return Histogram(bins=bins, range=range).symbolic_call(x)

    x = backend.convert_to_tensor(x)
    if len(x.shape) > 1:
        raise ValueError(
            "Input tensor must be 1-dimensional. "
            f"Received: input.shape={x.shape}"
        )
    return backend.numpy.histogram(x, bins=bins, range=range)