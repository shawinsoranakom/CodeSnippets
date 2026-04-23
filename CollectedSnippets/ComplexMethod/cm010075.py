def meta_sparse_structured_addmm(
    input: Tensor,
    mat1: Tensor,
    mat1_meta: Tensor,
    mat2: Tensor,
    *,
    alpha=1,
    beta=1,
    out_dtype: torch.dtype | None = None,
):
    if len(input.shape) != 1:
        raise AssertionError(
            f"only input broadcasted to columns of mat1 * mat2 product is supported, got {len(input.shape)}D input"
        )
    if len(mat1.shape) != 2:
        raise AssertionError(f"mat1 must be 2D, got {len(mat1.shape)}D")
    if len(mat1_meta.shape) != 2:
        raise AssertionError(f"mat1_meta must be 2D, got {len(mat1_meta.shape)}D")
    if len(mat2.shape) != 2:
        raise AssertionError(f"mat2 must be 2D, got {len(mat2.shape)}D")
    if input.size(0) != mat1.size(0):
        raise AssertionError(
            f"only input broadcasted to columns of mat1 * mat2 product is supported, "
            f"input.size(0)={input.size(0)} != mat1.size(0)={mat1.size(0)}"
        )
    if mat1.size(1) != mat2.size(0) / 2:
        raise AssertionError(
            f"mat1.size(1)={mat1.size(1)} != mat2.size(0)/2={mat2.size(0) / 2}"
        )
    output_sizes = [mat1.size(0), mat2.size(1)]

    if out_dtype is not None:
        if not (mat2.dtype == torch.int8 and out_dtype == torch.int32):
            raise AssertionError(
                f"out_dtype is only supported for i8i8->i32 linear operator, got mat2.dtype={mat2.dtype}, out_dtype={out_dtype}"
            )
    output = mat2.new_empty(
        output_sizes,
        dtype=mat2.dtype if out_dtype is None else out_dtype,
    )

    return output