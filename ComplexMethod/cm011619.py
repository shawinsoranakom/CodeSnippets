def matrix_norm(
    A: TensorLikeType,
    ord: float | str = "fro",
    dim: DimsType = (-2, -1),
    keepdim: bool = False,
    *,
    dtype: torch.dtype | None = None,
) -> TensorLikeType:
    # shape
    check_is_matrix(A, "linalg.matrix_norm")
    # dim

    dim = utils.canonicalize_dims(A.ndim, dim)
    if isinstance(dim, Dim):
        dim = (dim,)  # type: ignore[assignment]
    torch._check(
        len(dim) == 2, lambda: f"linalg.matrix_norm: dim must be a 2-tuple. Got {dim}"
    )
    torch._check(
        # pyrefly: ignore [bad-index]
        dim[0] != dim[1],
        # pyrefly: ignore [bad-index, index-error]
        # pyrefly: ignore [bad-index, index-error]
        lambda: f"linalg.matrix_norm: dims must be different. Got ({dim[0]}, {dim[1]})",
    )
    # dtype arg
    _check_norm_dtype(dtype, A.dtype, "linalg.matrix_norm")

    if isinstance(ord, str):
        # ord
        torch._check(
            ord in ("fro", "nuc"),
            lambda: f"linalg.matrix_norm: Order {ord} not supported.",
        )
        # dtype
        check_fp_or_complex(
            A.dtype, "linalg.matrix_norm", allow_low_precision_dtypes=ord != "nuc"
        )

        if ord == "fro":
            return vector_norm(A, 2, dim, keepdim, dtype=dtype)
        else:  # ord == "nuc"
            if dtype is not None:
                A = _maybe_convert_to_dtype(A, dtype)  # type: ignore[assignment]
            # pyrefly: ignore [bad-index, index-error]
            perm = _backshift_permutation(dim[0], dim[1], A.ndim)
            result = torch.sum(svdvals(prims.transpose(A, perm)), -1, keepdim)
            if keepdim:
                inv_perm = _inverse_permutation(perm)
                result = prims.transpose(torch.unsqueeze(result, -1), inv_perm)
            return result
    else:
        # ord
        abs_ord = abs(ord)
        torch._check(
            abs_ord in (2, 1, float("inf")),
            lambda: f"linalg.matrix_norm: Order {ord} not supported.",
        )
        # dtype
        check_fp_or_complex(
            A.dtype, "linalg.matrix_norm", allow_low_precision_dtypes=ord != 2
        )

        max_min = partial(torch.amax if ord > 0.0 else torch.amin, keepdim=keepdim)

        def _max_min_wrapper(A, dim):
            # pyrefly: ignore [unsupported-operation]
            if A.size(dim) == 0 and ord > 0.0:
                new_size = list(A.size())
                if keepdim:
                    new_size[dim] = 1
                else:
                    del new_size[dim]
                return torch.zeros(new_size, dtype=A.dtype, device=A.device)
            else:
                return max_min(A, dim)

        if abs_ord == 2.0:
            if dtype is not None:
                A = _maybe_convert_to_dtype(A, dtype)  # type: ignore[assignment]
            # pyrefly: ignore [bad-index, index-error]
            perm = _backshift_permutation(dim[0], dim[1], A.ndim)
            result = _max_min_wrapper(svdvals(prims.transpose(A, perm)), dim=-1)
            if keepdim:
                inv_perm = _inverse_permutation(perm)
                result = prims.transpose(torch.unsqueeze(result, -1), inv_perm)
            return result
        else:  # 1, -1, inf, -inf
            # pyrefly: ignore [bad-unpacking]
            dim0, dim1 = dim
            if abs_ord == float("inf"):
                dim0, dim1 = dim1, dim0
            if not keepdim and (dim0 < dim1):
                dim1 -= 1
            return _max_min_wrapper(
                vector_norm(A, 1.0, dim=dim0, keepdim=keepdim, dtype=dtype), dim1
            )