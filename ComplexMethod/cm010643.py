def max_pool2d(
    input: list[int],
    kernel_size: list[int],
    stride: list[int],
    padding: list[int],
    dilation: list[int],
    ceil_mode: bool,
):
    if not (len(kernel_size) == 1 or len(kernel_size) == 2):
        raise AssertionError(
            "max_pool2d: kernel_size must either be a single int, or a tuple of two ints"
        )
    kH = kernel_size[0]
    kW = kH if len(kernel_size) == 1 else kernel_size[1]

    if not (len(stride) == 0 or len(stride) == 1 or len(stride) == 2):
        raise AssertionError(
            "max_pool2d: stride must either be omitted, a single int, or a tuple of two ints"
        )
    dH = kH if len(stride) == 0 else stride[0]
    if len(stride) == 0:
        dW = kW
    elif len(stride) == 1:
        dW = dH
    else:
        dW = stride[1]

    if not (len(padding) == 1 or len(padding) == 2):
        raise AssertionError(
            "max_pool2d: padding must either be a single int, or a tuple of two ints"
        )
    padH = padding[0]
    padW = padH if len(padding) == 1 else padding[1]

    if not (len(dilation) == 1 or len(dilation) == 2):
        raise AssertionError(
            "max_pool2d: dilation must be either a single int, or a tuple of two ints"
        )
    dilationH = dilation[0]
    dilationW = dilationH if len(dilation) == 1 else dilation[1]

    if not (len(input) == 3 or len(input) == 4):
        raise AssertionError(f"Expected input length 3 or 4, but got {len(input)}")

    nbatch = input[-4] if len(input) == 4 else 1
    nInputPlane = input[-3]
    inputHeight = input[-2]
    inputWidth = input[-1]

    outputHeight = pooling_output_shape(inputHeight, kH, padH, dH, dilationH, ceil_mode)
    outputWidth = pooling_output_shape(inputWidth, kW, padW, dW, dilationW, ceil_mode)

    pool2d_shape_check(
        input,
        kH,
        kW,
        dH,
        dW,
        padH,
        padW,
        dilationH,
        dilationW,
        nInputPlane,
        inputHeight,
        inputWidth,
        outputHeight,
        outputWidth,
    )

    if len(input) == 3:
        return [nInputPlane, outputHeight, outputWidth]
    else:
        return [nbatch, nInputPlane, outputHeight, outputWidth]