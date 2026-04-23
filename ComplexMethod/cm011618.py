def vector_norm(
    x: TensorLikeType,
    ord: float | int = 2,
    dim: DimsType | None = None,
    keepdim: bool = False,
    *,
    dtype: torch.dtype | None = None,
) -> Tensor:
    from torch.fx.experimental.symbolic_shapes import guard_or_false

    check_fp_or_complex(x.dtype, "linalg.vector_norm")

    if isinstance(dim, Dim):
        dim = [dim]  # type: ignore[assignment]

    _check_vector_norm_args(x, ord, dim)

    _check_norm_dtype(dtype, x.dtype, "linalg.vector_norm")

    computation_dtype, result_dtype = utils.reduction_dtypes(
        x, utils.REDUCTION_OUTPUT_TYPE_KIND.COMPLEX_TO_FLOAT, dtype
    )

    to_result_dtype = partial(_maybe_convert_to_dtype, dtype=result_dtype)

    # Implementation
    if ord == 0.0:
        return torch.sum(torch.ne(x, 0.0), dim=dim, keepdim=keepdim, dtype=result_dtype)
    elif ord == float("inf"):
        return to_result_dtype(torch.amax(torch.abs(x), dim=dim, keepdim=keepdim))  # type: ignore[return-value,arg-type]
    elif ord == float("-inf"):
        return to_result_dtype(torch.amin(torch.abs(x), dim=dim, keepdim=keepdim))  # type: ignore[return-value,arg-type]
    else:
        # From here on the computation dtype is important as the reduction is non-trivial
        x = _maybe_convert_to_dtype(x, computation_dtype)  # type: ignore[assignment]
        reduce_sum = partial(torch.sum, dim=dim, keepdim=keepdim)

        is_ord_even = ord % 2 == 0 if isinstance(ord, IntLike) else ord % 2.0 == 0.0
        if dim == []:
            dim = None

        if (dim is None and guard_or_false(x.numel() == 1)) or (
            dim is not None
            and (x.ndim > 0 and all(guard_or_false(x.shape[d] == 1) for d in dim))
        ):
            if x.ndim > 64:
                raise RuntimeError(
                    f"Received a tensor with {x.ndim} dimensions, but only tensors with up to 64 dims are supported!"
                )
            x = torch.abs(x)
            if keepdim or x.ndim == 0:
                return to_result_dtype(x).contiguous()
            elif dim is None:
                return to_result_dtype(x).flatten()[0]
            else:
                new_shape = [s for d, s in enumerate(x.shape) if d not in dim]
                return to_result_dtype(x.view(new_shape)).contiguous()

        if not (is_ord_even and utils.is_float_dtype(x.dtype)):
            x = torch.abs(x)
        return to_result_dtype(torch.pow(reduce_sum(torch.pow(x, ord)), 1.0 / ord))