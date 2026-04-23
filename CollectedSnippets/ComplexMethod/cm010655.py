def var_decomposition(
    input: Tensor,
    dim: list[int] | None = None,
    correction: Number | None = None,
    keepdim: bool = False,
) -> Tensor:
    if dim is None:
        dim_i: list[int] = []
        dim = dim_i

    if isinstance(dim, (tuple, list)) and len(dim) == 0:
        n = input.numel()
    else:
        n = 1
        for dim_i in dim:  # type: ignore[assignment]
            n *= input.shape[dim_i]  # type: ignore[call-overload]

    mean = aten.mean(input, dim, True)
    sub = input - mean
    sq = sub * sub
    sum = aten.sum(sq, dim, keepdim)

    if correction is None:
        denom = float(n - 1)
    else:
        if isinstance(correction, int):
            denom = float(n - correction)
        elif isinstance(correction, float):
            denom = float(n) - correction
        else:
            raise RuntimeError("correction must be int or float")

    # pyrefly: ignore [no-matching-overload]
    return sum / max(0, denom)