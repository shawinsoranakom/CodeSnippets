def pool2d_shape_check(
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
    memory_format,
):
    ndim = input.dim()
    nOutputPlane = nInputPlane

    torch._check(
        kW > 0 and kH > 0,
        lambda: f"kernel size should be greater than zero, but got kH: {kH}, kW: {kW}",
    )
    torch._check(
        dW > 0 and dH > 0,
        lambda: f"stride should be greater than zero, but got dH: {dH}, dW: {dW}",
    )
    torch._check(
        dilationH > 0 and dilationW > 0,
        lambda: f"dilation should be greater than zero, but got dilationH: {dilationH}, dilationW: {dilationW}",
    )

    valid_dims = input.size(1) != 0 and input.size(2) != 0

    if memory_format == torch.channels_last:
        torch._check(
            ndim == 4 and valid_dims and input.size(3) != 0,
            lambda: "Expected 4D (batch mode) tensor expected for input with channels_last layout"
            f" with optional 0 dim batch size for input, but got: {input.size()}",
        )
    else:
        torch._check(
            (ndim == 3 and input.size(0) != 0 and valid_dims)
            or (ndim == 4 and valid_dims and input.size(3) != 0),
            lambda: f"Expected 3D or 4D (batch mode) tensor with optional 0 dim batch size for input, but got: {input.size()}",
        )

    torch._check(
        kW // 2 >= padW and kH // 2 >= padH,
        lambda: "pad should be smaller than or equal to half of kernel size, but got "
        f"padW = {padW}, padH = {padH}, kW = {kW}, kH = {kH}",
    )

    torch._check(
        outputWidth >= 1 and outputHeight >= 1,
        lambda: f"Given input size: ({nInputPlane}x{inputHeight}x{inputWidth}). "
        f"Calculated output size: ({nOutputPlane}x{outputHeight}x{outputWidth}). "
        "Output size is too small",
    )