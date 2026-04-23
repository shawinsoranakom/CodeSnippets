def _check_vector_norm_args(
    x: TensorLikeType, ord: float | int = 2, dim: DimsType | None = None
):
    from torch.fx.experimental.symbolic_shapes import sym_or

    if not (ord < 0.0 or ord == float("inf")):
        return

    torch._check(
        sym_or(
            x.numel() != 0,
            not isinstance(dim, IntLike) and dim is not None and len(dim) != 0,
        ),
        lambda: f"linalg.vector_norm cannot compute the {ord} norm on an empty tensor "
        "because the operation does not have an identity",
    )

    shape = x.shape
    if dim is not None and not isinstance(dim, IntLike):
        for d in dim:
            torch._check(
                sym_or(x.numel() != 0, d < len(shape) and d >= 0 and shape[d] != 0),
                lambda: f"linalg.vector_norm cannot compute the {ord} norm on the "
                f"dimension {d} because this dimension is empty and the "
                "operation does not have an identity",
            )