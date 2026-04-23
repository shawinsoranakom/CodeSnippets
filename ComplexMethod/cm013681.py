def _enforce_mem_layouts(
    query: Tensor, key: Tensor, value: Tensor
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """
    Enforce memory layouts for query, key, and value tensors.

    For non-FP8 dtypes, no action is taken.

    For FP8 dtypes, we enforce the following memory layouts:
    - Query tensor must be in row-major memory layout, as it will be the left-operand in the FP8 GEMM `q @ k.T`.
    - Key tensor must be in row-major memory layout, as it will be transposed when used as the right-operand
      in the FP8 GEMM `q @ k.T`, meaning it will correctly be in column-major memory layout for the GEMM.
    - Value tensor must be in column-major memory layout, as it will be the right-operand in the FP8 GEMM `softmax_scores @ v`.

    Returns the query, key, and value tensors with the enforced memory layouts.
    """

    def is_row_major(tensor: Tensor) -> bool:
        return tensor.stride()[-1] == 1

    def is_col_major(tensor: Tensor) -> bool:
        return tensor.stride()[-2] == 1

    # These memory layout constraint are only for FP8 GEMMs on NVIDIA GPU architectures >= SM89 and < SM100.
    # This is because GPU arch < SM89 does not not support FP8 GEMMs, and
    # SM100 has support for TN, NT, TT, NN layouts for FP8 GEMMs
    # (i.e., left and right operands can be in row or column major layouts)
    # so this check is only needed for older architectures.
    # See: https://github.com/NVIDIA/cutlass/blob/main/media/docs/cpp/blackwell_functionality.md
    fp8_dtypes = (
        torch.float8_e4m3fn,
        torch.float8_e5m2,
    )
    gemm_precision = query.dtype

    should_enforce_mem_layout = (
        gemm_precision in fp8_dtypes
        and torch.version.cuda is not None
        and torch.cuda.get_device_capability("cuda") >= (8, 9)
        and torch.cuda.get_device_capability("cuda") < (10, 0)
    )
    if not should_enforce_mem_layout:
        return query, key, value

    # Query must be in row-major memory layout as the left-operand in the FP8 GEMM `q @ k.T`
    if not is_row_major(query):
        query = query.contiguous()

    # Key must be in row-major memory layout as it will be transposed when used as the right-operand
    # in the FP8 GEMM `q @ k.T`, meaning it will correctly be in column-major memory layout for the GEMM.
    if not is_row_major(key):
        key = key.contiguous()

    # Value must be in column-major memory layout as the right-operand in the FP8 GEMM `softmax_scores @ v`
    if not is_col_major(value):
        value = value.transpose(-2, -1).contiguous().transpose(-2, -1)
    return query, key, value