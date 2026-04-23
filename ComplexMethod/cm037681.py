def silu_mul_per_token_group_quant_fp8_colmajor(
    input: torch.Tensor,  # [M, N]
    output: torch.Tensor | None = None,  # [M, N // 2]
    use_ue8m0: bool | None = None,
    eps: float = 1e-10,
):
    """
    silu+mul + block-fp8 quant with group size 128.
    """
    GROUP_SIZE = 128
    assert input.ndim == 2
    if output is not None:
        assert output.ndim == 2
    assert input.size(0) % GROUP_SIZE == 0
    assert input.size(1) % (GROUP_SIZE * 2) == 0

    if use_ue8m0 is None:
        use_ue8m0 = is_deep_gemm_e8m0_used()

    M, N = input.size()
    N_2 = N // 2

    fp8_dtype = current_platform.fp8_dtype()
    if output is None:
        output = torch.empty((M, N_2), dtype=fp8_dtype, device=input.device)

    output_scales = torch.empty(
        ((N_2 // GROUP_SIZE), M), dtype=torch.float32, device=input.device
    ).transpose(0, 1)

    BLOCK_M = 8
    BLOCK_N = GROUP_SIZE
    assert M % BLOCK_M == 0
    assert N_2 % BLOCK_N == 0

    # Using the default value (240.0) from pytorch will cause accuracy
    # issue on dynamic quantization models. Here use 224.0 for fnuz on ROCm
    # platforms that use the torch.float8_e4m3fnuz dtype.
    finfo = torch.finfo(fp8_dtype)
    fp8_min = -224.0 if current_platform.is_fp8_fnuz() else finfo.min
    fp8_max = 224.0 if current_platform.is_fp8_fnuz() else finfo.max

    # Force even division so we can avoid edgecases within the kernel.
    assert M % BLOCK_M == 0
    assert N_2 % BLOCK_N == 0
    grid = (M // BLOCK_M, N_2 // BLOCK_N)

    _silu_mul_per_token_group_quant_fp8_colmajor[grid](
        input,
        output,
        output_scales,
        M,
        N,
        output_scales.stride(-1),
        eps,
        fp8_min,
        fp8_max,
        use_ue8m0,
        GROUP_SIZE,
        BLOCK_M,
        BLOCK_N,
    )

    return output, output_scales