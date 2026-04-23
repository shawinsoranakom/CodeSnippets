def flashinfer_scaled_fp4_mm(
    a: torch.Tensor,
    b: torch.Tensor,
    block_scale_a: torch.Tensor,
    block_scale_b: torch.Tensor,
    alpha: torch.Tensor,
    out_dtype: torch.dtype,
    backend: str,
) -> torch.Tensor:
    assert a.ndim == 2 and b.ndim == 2
    assert block_scale_a.ndim == 2 and block_scale_b.ndim == 2
    assert a.stride(-1) == 1 and b.stride(-1) == 1
    assert a.shape[1] == b.shape[1]

    if backend in ("cutlass", "cudnn"):
        block_scale_a = block_scale_a.view(torch.uint8)
        block_scale_b = block_scale_b.view(torch.uint8)

    use_8x4_sf_layout = True if backend == "trtllm" and a.shape[0] <= 32 else False  # noqa: SIM210

    return flashinfer_mm_fp4(
        a,
        b.t(),
        block_scale_a,
        block_scale_b.t(),
        alpha,
        out_dtype,
        use_8x4_sf_layout=use_8x4_sf_layout,
        backend=backend,
    )