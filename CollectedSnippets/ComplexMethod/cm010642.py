def pool2d_shape_check(
    input: list[int],
    kH: int,
    kW: int,
    dH: int,
    dW: int,
    padH: int,
    padW: int,
    dilationH: int,
    dilationW: int,
    nInputPlane: int,
    inputHeight: int,
    inputWidth: int,
    outputHeight: int,
    outputWidth: int,
):
    ndim = len(input)

    if not (kW > 0 and kH > 0):
        raise AssertionError(f"Expected kW ({kW}) > 0 and kH ({kH}) > 0")
    if not (dW > 0 and dH > 0):
        raise AssertionError(f"Expected dW ({dW}) > 0 and dH ({dH}) > 0")
    if not (dilationH > 0 and dilationW > 0):
        raise AssertionError(
            f"Expected dilationH ({dilationH}) > 0 and dilationW ({dilationW}) > 0"
        )

    valid_dims = input[1] != 0 and input[2] != 0
    if not (
        ndim == 3
        and input[0] != 0
        and valid_dims
        or (ndim == 4 and valid_dims and input[3] != 0)
    ):
        raise AssertionError(f"Invalid input dimensions: ndim={ndim}, input={input}")

    if not (kW // 2 >= padW and kH // 2 >= padH):
        raise AssertionError(
            f"Expected kW//2 ({kW // 2}) >= padW ({padW}) and "
            f"kH//2 ({kH // 2}) >= padH ({padH})"
        )
    if not (outputWidth >= 1 and outputHeight >= 1):
        raise AssertionError(
            f"Expected outputWidth ({outputWidth}) >= 1 and "
            f"outputHeight ({outputHeight}) >= 1"
        )