def filter(layout: Layout, profile: LayoutProfile = None) -> Layout:
    if is_tuple(profile):
        if len(layout) < len(profile):
            raise AssertionError
        return make_layout(
            # pyrefly: ignore [bad-argument-type]
            chain(
                (filter(layout[i], profile[i]) for i in range(len(profile))),  # type: ignore[arg-type]
                (layout[i] for i in range(len(profile), len(layout))),
            )
        )

    result_shape = []
    result_stride = []
    for shape, stride in zip(flatten(layout.shape), flatten(layout.stride)):
        # skip their shape-1s and stride-0s
        if not (shape == 1 or stride == 0):
            result_shape.append(shape)
            result_stride.append(stride)

    if len(result_shape) == 0:
        return Layout(1, 0)
    else:
        return coalesce(Layout(tuple(result_shape), tuple(result_stride)))