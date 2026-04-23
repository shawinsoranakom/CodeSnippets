def meta__cslt_sparse_mm(
    compressed_A: torch.Tensor,
    dense_B: torch.Tensor,
    bias: Tensor | None = None,
    alpha: Tensor | None = None,
    out_dtype: torch.dtype | None = None,
    transpose_result: bool = False,
    alg_id: int = 0,
    split_k: int = 1,
    split_k_mode: int = -1,
):
    if dense_B.dtype not in {
        torch.float32,
        torch.float16,
        torch.bfloat16,
        torch.int8,
        torch.float8_e4m3fn,
    }:
        raise AssertionError(
            f"_cslt_sparse_mm only supports fp16, bf16, int8, and fp8e4m3, got {dense_B.dtype}"
        )
    if compressed_A.dtype != dense_B.dtype:
        raise AssertionError(
            f"inputs must have the same dtype, got {compressed_A.dtype} and {dense_B.dtype}"
        )
    if len(dense_B.shape) != 2:
        raise AssertionError(
            f"_cslt_sparse_mm only supports 2d inputs, got {len(dense_B.shape)}D"
        )

    is_8bit_input_type = compressed_A.dtype in [torch.int8, torch.float8_e4m3fn]

    if is_8bit_input_type:
        if dense_B.is_contiguous():
            raise AssertionError("dense input must be transposed for 8bit dtypes")

    n = dense_B.size(1)
    m = compressed_A.size(0)
    if bias is not None:
        if m != bias.size(0):
            raise AssertionError(
                f"bias size mismatch: m={m} != bias.size(0)={bias.size(0)}"
            )

    if out_dtype is not None:
        if not (
            is_8bit_input_type
            and out_dtype
            in {
                torch.float16,
                torch.bfloat16,
                torch.int32,
                torch.float8_e4m3fn,
            }
        ):
            raise AssertionError(
                f"out_dtype is not supported for {compressed_A.dtype} x {dense_B.dtype} -> {out_dtype} matmul!"
            )
    output_shape = (n, m) if transpose_result else (m, n)
    return dense_B.new_empty(output_shape, dtype=out_dtype)