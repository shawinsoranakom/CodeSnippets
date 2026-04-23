def flashinfer_scaled_fp8_mm(
    a: torch.Tensor,
    b: torch.Tensor,
    scale_a: torch.Tensor,
    scale_b: torch.Tensor,
    out_dtype: torch.dtype,
    bias: torch.Tensor | None = None,
) -> torch.Tensor:
    assert a.ndim == 2 and b.ndim == 2
    assert a.shape[1] == b.shape[0]
    assert scale_a.numel() == 1 and scale_b.numel() == 1
    assert a.dtype == torch.float8_e4m3fn and b.dtype == torch.float8_e4m3fn
    assert a.device.type == "cuda" and b.device.type == "cuda"
    assert scale_a.dtype == torch.float32 and scale_b.dtype == torch.float32
    assert scale_a.device.type == "cuda" and scale_b.device.type == "cuda"

    output = bmm_fp8(
        a.unsqueeze(0),
        b.unsqueeze(0),
        scale_a,
        scale_b,
        out_dtype,
        "auto",
    ).view(a.shape[0], b.shape[1])

    if bias is not None:
        output = output + bias
    return output