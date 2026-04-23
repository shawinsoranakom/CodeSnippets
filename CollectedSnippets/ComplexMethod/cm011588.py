def mean(
    a: TensorLikeType,
    dim: DimsType | None = None,
    keepdim: bool = False,
    *,
    dtype=None,
    out=None,
) -> TensorLikeType:
    # reduces over all dimensions if dim=() is passed
    if dim == () or dim == []:
        dim = None
    orig_dtype = dtype
    if dtype is None:
        dtype = a.dtype
    result = _reduction(
        a,
        prims.sum,
        dims=dim,
        keepdims=keepdim,
        dtype=dtype,
        out=None,
        output_dtype_kind=REDUCTION_OUTPUT_TYPE_KIND.KEEP_PROMOTED_TYPE,
    )
    torch._check(
        utils.is_float_dtype(dtype) or utils.is_complex_dtype(dtype),
        lambda: (
            f"mean(): could not infer output dtype. "
            f"{'Input' if orig_dtype is None else 'Optional'} dtype must be either "
            f"a floating point or complex dtype. Got: {dtype}"
        ),
    )
    if isinstance(dim, Dim):
        dim = (dim,)  # type: ignore[assignment]
    dims = utils.reduction_dims(a.shape, dim)  # type: ignore[arg-type]
    nelem = 1 if a.ndim == 0 else reduce(operator.mul, (a.shape[i] for i in dims), 1)
    result = true_divide(result, nelem)
    result_dtype = a.dtype if dtype is None else dtype
    result = _maybe_convert_to_dtype(result, result_dtype)  # type: ignore[method-assign]
    if out is not None:
        if not isinstance(out, TensorLike):
            raise AssertionError(f"out must be TensorLike, got {type(out)}")
        out = _maybe_resize_out(out, result.shape)
        return _safe_copy_out(copy_from=result, copy_to=out)  # type: ignore[arg-type]
    return result