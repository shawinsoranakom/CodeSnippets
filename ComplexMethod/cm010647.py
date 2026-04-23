def check_shape_forward(
    input: list[int],
    weight_sizes: list[int],
    bias: Optional[list[int]],
    stride: list[int],
    padding: list[int],
    dilation: list[int],
    groups: int,
):
    k = len(input)
    weight_dim = len(weight_sizes)

    # TODO: assertions could be expanded with the error messages
    if check_non_negative(padding):
        raise AssertionError(f"Padding must be non-negative, got {padding}")
    if check_non_negative(stride):
        raise AssertionError(f"Stride must be non-negative, got {stride}")

    if weight_dim != k:
        raise AssertionError(f"Expected weight_dim ({weight_dim}) == k ({k})")
    if weight_sizes[0] < groups:
        raise AssertionError(
            f"Expected weight_sizes[0] ({weight_sizes[0]}) >= groups ({groups})"
        )
    if (weight_sizes[0] % groups) != 0:
        raise AssertionError(
            f"Expected weight_sizes[0] ({weight_sizes[0]}) to be divisible by "
            f"groups ({groups})"
        )
    # only handling not transposed
    if input[1] != weight_sizes[1] * groups:
        raise AssertionError(
            f"Expected input[1] ({input[1]}) == weight_sizes[1] * groups "
            f"({weight_sizes[1] * groups})"
        )
    if bias is not None and not (len(bias) == 1 and bias[0] == weight_sizes[0]):
        raise AssertionError(
            f"Expected bias to be None or have shape [1] with value "
            f"weight_sizes[0]={weight_sizes[0]}, got {bias}"
        )

    for i in range(2, k):
        if (input[i] + 2 * padding[i - 2]) < (
            dilation[i - 2] * (weight_sizes[i] - 1) + 1
        ):
            raise AssertionError(
                f"Calculated padded input size ({input[i] + 2 * padding[i - 2]}) "
                f"is smaller than effective kernel size "
                f"({dilation[i - 2] * (weight_sizes[i] - 1) + 1}) at dimension {i}"
            )