def unique(
    x,
    sorted=True,
    return_inverse=False,
    return_counts=False,
    axis=None,
    size=None,
    fill_value=None,
):
    # Note: np.unique always sorts the output in versions < 2.3.0.
    # We accept the 'sorted' argument for API consistency across backends
    # but do not pass it to np.unique to avoid TypeError in older versions.
    output = np.unique(
        x,
        return_inverse=return_inverse,
        return_counts=return_counts,
        axis=axis,
        equal_nan=False,
    )

    if not (return_inverse or return_counts):
        output = [output]
    else:
        output = list(output)

    values = output[0]

    if size is not None:
        dim = axis if axis is not None else 0
        values_count = values.shape[dim]

        if values_count > size:
            # Truncate
            indices = [slice(None)] * values.ndim
            indices[dim] = slice(0, size)
            values = values[tuple(indices)]
            if return_counts:
                output[-1] = output[-1][tuple(indices)]

        elif values_count < size:
            # Pad
            pad_width = [(0, 0)] * values.ndim
            pad_width[dim] = (0, size - values_count)
            fill = 0 if fill_value is None else fill_value
            values = np.pad(values, pad_width, constant_values=fill)
            if return_counts:
                output[-1] = np.pad(output[-1], pad_width, constant_values=0)

    output[0] = values
    return output[0] if len(output) == 1 else tuple(output)