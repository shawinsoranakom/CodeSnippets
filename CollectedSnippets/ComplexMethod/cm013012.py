def _adjust_attributes_of_max_pool(
    expand_size: int,
    kernel_size: Sequence[int] | int,
    stride: Sequence[int] | int,
    padding: Sequence[int] | int,
    dilation: Sequence[int] | int,
) -> tuple[Sequence[int], Sequence[int], Sequence[int], Sequence[int]]:
    """Adjust attributes of avg_pool to match ONNX specification."""

    if isinstance(dilation, int):
        dilation = [dilation] * expand_size

    if isinstance(kernel_size, int):
        kernel_shape = [kernel_size] * expand_size
    else:
        kernel_shape = kernel_size  # type: ignore[assignment]

    if isinstance(padding, int):
        pads = [padding] * expand_size * 2  # type: ignore[operator, assignment]
    elif len(padding) == 1:
        pads = padding * expand_size * 2  # type: ignore[operator, assignment]
    elif len(padding) == 2:
        # 2D padding
        pads = padding * 2  # type: ignore[operator, assignment]
    elif len(padding) == 3:
        # 3D padding
        pads = padding * 2  # type: ignore[operator, assignment]
    else:
        # When padding is already done for all dimensions,
        # we don't need to double it
        # eg: (1, 1, 1, 1, 1, 1)
        pads = padding  # type: ignore[assignment]

    if isinstance(stride, int):
        strides = [stride] * expand_size
    elif not stride:
        strides = kernel_shape
    else:
        strides = stride  # type: ignore[assignment]

    # pyrefly: ignore [bad-return]
    return (kernel_shape, strides, pads, dilation)