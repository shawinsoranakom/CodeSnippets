def tensor_conv(
    draw, spatial_dim=2, batch_size_range=(1, 4),
    input_channels_per_group_range=(3, 7),
    output_channels_per_group_range=(3, 7), feature_map_range=(6, 12),
    kernel_range=(3, 7), max_groups=1, can_be_transposed=False,
    elements=None, qparams=None
):

    # Resolve the minibatch, in_channels, out_channels, iH/iW, iK/iW
    batch_size = draw(st.integers(*batch_size_range))
    input_channels_per_group = draw(
        st.integers(*input_channels_per_group_range))
    output_channels_per_group = draw(
        st.integers(*output_channels_per_group_range))
    groups = draw(st.integers(1, max_groups))
    input_channels = input_channels_per_group * groups
    output_channels = output_channels_per_group * groups

    if isinstance(spatial_dim, Iterable):
        spatial_dim = draw(st.sampled_from(spatial_dim))

    feature_map_shape = [draw(st.integers(*feature_map_range)) for _ in range(spatial_dim)]

    kernels = [draw(st.integers(*kernel_range)) for _ in range(spatial_dim)]

    tr = False
    weight_shape = (output_channels, input_channels_per_group) + tuple(kernels)
    bias_shape = output_channels
    if can_be_transposed:
        tr = draw(st.booleans())
        if tr:
            weight_shape = (input_channels, output_channels_per_group) + tuple(kernels)
            bias_shape = output_channels

    # Resolve the tensors
    if qparams is not None:
        if isinstance(qparams, (list, tuple)):
            if len(qparams) != 3:
                raise AssertionError("Need 3 qparams for X, w, b")
        else:
            qparams = [qparams] * 3

    X = draw(tensor(shapes=(
        (batch_size, input_channels) + tuple(feature_map_shape),),
        elements=elements, qparams=qparams[0]))
    W = draw(tensor(shapes=(weight_shape,), elements=elements,
                    qparams=qparams[1]))
    b = draw(tensor(shapes=(bias_shape,), elements=elements,
                    qparams=qparams[2]))

    return X, W, b, groups, tr