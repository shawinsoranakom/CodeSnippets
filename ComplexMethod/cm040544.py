def _compute_split_output_spec(x, indices_or_sections, axis):
    x_shape = list(x.shape)
    x_size_on_axis = x_shape[axis]
    if isinstance(indices_or_sections, int):
        if x_size_on_axis is None:
            x_shape[axis] = None
            return [
                KerasTensor(x_shape, dtype=x.dtype)
                for _ in range(indices_or_sections)
            ]

        if np.mod(x_size_on_axis, indices_or_sections) != 0:
            raise ValueError(
                "`x` size on given `axis` must be divisible by "
                "`indices_or_sections` when `indices_or_sections` is an "
                f"int. But received {x_size_on_axis} and "
                f"{indices_or_sections}."
            )

        size = x_size_on_axis // indices_or_sections
        x_shape[axis] = size
        return [
            KerasTensor(x_shape, dtype=x.dtype)
            for _ in range(indices_or_sections)
        ]

    all_indices = [0] + list(indices_or_sections) + [x_size_on_axis]
    outputs = []

    for i in range(len(all_indices) - 1):
        start = all_indices[i]
        end = all_indices[i + 1]
        if start is None or end is None:
            output_size = None
        else:
            output_size = end - start
        output_shape = list(x_shape)
        output_shape[axis] = output_size
        outputs.append(KerasTensor(output_shape, dtype=x.dtype))

    return outputs