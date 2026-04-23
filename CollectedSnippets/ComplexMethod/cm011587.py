def _reduction(
    a: TensorLikeType,
    prim: Callable,
    *,
    has_identity: bool = True,
    accepts_dim_tuple: bool = True,  # to handle min/argmin that accept single dim only
    dims: DimsType | None = None,
    keepdims: bool = False,
    dtype: torch.dtype | None = None,  # should be specified for ops that support it
    out: Tensor | None = None,
    output_dtype_kind: REDUCTION_OUTPUT_TYPE_KIND,
) -> TensorLikeType:  # it is usually SAME, but I want
    # ref writers to actually think about what to put here
    if not isinstance(a, TensorLike):
        raise AssertionError(f"a must be TensorLike, got {type(a)}")
    if a.ndim > 64:
        raise RuntimeError(
            f"Received a tensor with {a.ndim} dimensions, but only tensors with up to 64 dims are supported!"
        )

    if out is not None:
        if not isinstance(out, TensorLike):
            raise AssertionError(f"out must be TensorLike, got {type(out)}")
        if dtype is not None:
            # TODO - this is true for eager mode currently, but it's wrong behavior for complex norms
            if dtype != out.dtype:
                raise RuntimeError(
                    "dtype argument and out dtype must match in reduction"
                )
    if not accepts_dim_tuple:
        if not (dims is None or isinstance(dims, Dim)):
            raise AssertionError(f"dims must be None or Dim, got {type(dims)}")
    if isinstance(dims, Dim):
        dims = (dims,)  # type: ignore[assignment]
    dims = utils.reduction_dims(a.shape, dims)
    if not has_identity:
        from torch.fx.experimental.symbolic_shapes import sym_and

        valid_shape = a.ndim == 0 or sym_and(*(a.shape[i] > 0 for i in dims))
        torch._check(
            valid_shape,
            lambda: "reducing over zero-size dimension for reduction operation without identity",
        )

    computation_dtype, result_dtype = utils.reduction_dtypes(
        a, output_dtype_kind, dtype
    )
    a = _maybe_convert_to_dtype(a, computation_dtype)  # type: ignore[method-assign]
    result = prim(a, dims)
    if keepdims:
        output_shape = [a.shape[i] if i not in dims else 1 for i in range(a.ndim)]
        broadcast_dims = [i for i in range(a.ndim) if i not in dims]
        result = prims.broadcast_in_dim(result, output_shape, broadcast_dims)

    if out is not None:
        if result_dtype is None:
            raise AssertionError("result_dtype should not be None when out is provided")
        if dtype is not None and result_dtype != out.dtype:
            raise RuntimeError(
                "Expected the dtype of reduction result and out to match"
            )
        out = _maybe_resize_out(out, result.shape)
        return _safe_copy_out(copy_from=result, copy_to=out)  # type: ignore[arg-type]

    if result.dtype != result_dtype and result_dtype is not None:
        result = prims.convert_element_type(result, result_dtype)

    return result