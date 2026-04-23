def upsample_nearest2d(
    input: list[int],
    output_size: Optional[list[int]],
    scale_factors: Optional[list[float]],
):
    out: list[int] = []
    out.append(input[0])
    out.append(input[1])

    if scale_factors is None and output_size is None:
        raise AssertionError("Either output_size or scale_factors must be presented")

    if output_size is not None:
        if scale_factors is not None:
            raise AssertionError(
                "Must specify exactly one of output_size and scale_factors"
            )
        if len(output_size) != 2:
            raise AssertionError(
                f"Expected output_size to have length 2, but got {len(output_size)}"
            )
        out.append(output_size[0])
        out.append(output_size[1])

    if scale_factors is not None:
        if output_size is not None:
            raise AssertionError(
                "Must specify exactly one of output_size and scale_factors"
            )
        if len(scale_factors) != 2:
            raise AssertionError(
                f"Expected scale_factors to have length 2, but got {len(scale_factors)}"
            )
        out.append(int(input[2] * scale_factors[0]))
        out.append(int(input[3] * scale_factors[1]))

    return out