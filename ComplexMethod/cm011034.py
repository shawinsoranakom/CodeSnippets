def coalesce(layout: Layout, profile: LayoutProfile = None) -> Layout:
    if is_tuple(profile):
        if len(layout) < len(profile):
            raise AssertionError
        return make_layout(
            # pyrefly: ignore [bad-argument-type]
            chain(
                (coalesce(layout[i], profile[i]) for i in range(len(profile))),  # type: ignore[arg-type]
                (layout[i] for i in range(len(profile), len(layout))),
            )
        )

    result_shape = [1]
    result_stride = [0]
    # Since we now follow lexicographic order, we need to process from right to left.
    # And to make implementation more efficient, we append to the end of list and reverse it in the end.
    for shape, stride in zip(
        reversed(flatten(layout.shape)), reversed(flatten(layout.stride))
    ):
        # skip their shape-1s
        if shape == 1:
            continue
        # replace our shape-1 with anything
        elif result_shape[-1] == 1:
            result_shape[-1] = shape
            result_stride[-1] = stride
        # merge modes if the shape*stride match
        elif result_shape[-1] * result_stride[-1] == stride:
            result_shape[-1] = result_shape[-1] * shape
        # append a new mode
        else:
            result_shape.append(shape)
            result_stride.append(stride)

    if len(result_shape) == 1:
        return Layout(result_shape[0], result_stride[0])
    else:
        result_shape.reverse()
        result_stride.reverse()
        return Layout(tuple(result_shape), tuple(result_stride))