def _create_axes_map(axes, input_shape, axes_lengths):
    axes_map = {}

    for axis, dim in zip(axes, input_shape):
        # Check for grouped axes pattern, e.g., "(h1 h)"
        grouped_axes = re.match(r"\(([\w\s]+)\)", axis)

        if grouped_axes:
            inner_axes = grouped_axes.group(1).split()
            known_axes = [a for a in inner_axes if a in axes_lengths]
            inferred_axes = [a for a in inner_axes if a not in axes_lengths]

            if inferred_axes:
                inferred_axis = inferred_axes[0]
                known_product = prod([axes_lengths[a] for a in known_axes])
                axes_lengths[inferred_axis] = dim // known_product

            axes_map.update({a: axes_lengths[a] for a in inner_axes})
        else:
            axes_map[axis] = dim

    return axes_map