def norm(
    A: TensorLikeType,
    ord: float | str | None = None,
    dim: DimsType | None = None,
    keepdim: bool = False,
    *,
    dtype: torch.dtype | None = None,
) -> TensorLikeType:
    if dim is not None:
        if isinstance(dim, Dim):
            dim = (dim,)  # type: ignore[assignment]
        torch._check(
            len(dim) in (1, 2),
            lambda: f"linalg.norm: If dim is specified, it must be of length 1 or 2. Got {dim}",
        )
    elif ord is not None:
        torch._check(
            A.ndim in (1, 2),
            lambda: f"linalg.norm: If dim is not specified but ord is, the input must be 1D or 2D. Got {A.ndim}D",
        )

    if ord is not None and (
        (dim is not None and len(dim) == 2) or (dim is None and A.ndim == 2)
    ):
        if dim is None:
            dim = (0, 1)
        return matrix_norm(A, ord, dim, keepdim, dtype=dtype)
    else:
        if ord is None:
            ord = 2.0
        return vector_norm(A, ord, dim, keepdim, dtype=dtype)