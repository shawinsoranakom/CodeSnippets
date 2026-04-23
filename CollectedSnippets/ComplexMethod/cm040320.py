def unique(
    x,
    sorted=True,
    return_inverse=False,
    return_counts=False,
    axis=None,
    size=None,
    fill_value=None,
):
    if not isinstance(x, torch.Tensor):
        x = torch.as_tensor(x)

    output = torch.unique(
        x,
        sorted=sorted,  # Added sorted parameter here
        return_inverse=return_inverse,
        return_counts=return_counts,
        dim=axis,
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
            diff = size - values_count
            pad_width = [0, 0] * values.ndim
            # F.pad expects padding from last dim to first
            idx = (values.ndim - 1 - dim) * 2
            pad_width[idx + 1] = diff
            fill = 0 if fill_value is None else fill_value
            values = torch.nn.functional.pad(values, pad_width, value=fill)
            if return_counts:
                output[-1] = torch.nn.functional.pad(
                    output[-1], pad_width, value=0
                )

    output[0] = values
    return output[0] if len(output) == 1 else tuple(output)