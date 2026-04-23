def ref_dynamic_per_token_quant(
    x: torch.Tensor, quant_dtype: torch.dtype, scale_ub: torch.Tensor | None = None
) -> tuple[torch.Tensor, torch.Tensor]:
    assert quant_dtype in [torch.int8, FP8_DTYPE]
    if scale_ub is not None:
        assert quant_dtype == FP8_DTYPE

    if quant_dtype == torch.int8:
        qtype_traits = torch.iinfo(quant_dtype)
        qtype_traits_min = qtype_traits.min
        qtype_traits_max = qtype_traits.max
    else:
        qtype_traits_min, qtype_traits_max = get_fp8_min_max()
    qtype_max = as_float32_tensor(qtype_traits_max)
    s_1 = as_float32_tensor(1.0)
    s_512 = as_float32_tensor(512.0)

    # For fp8, in order to match the cuda kernel output, we have to do exactly
    # the same operations as in the corresponding fp8 kernel to prevent
    # rounding errors.

    # Compute scales
    x_token_max, _ = x.abs().max(dim=-1)
    x_token_max = as_float32_tensor(x_token_max)
    if scale_ub is not None:
        x_token_max = x_token_max.clamp(max=scale_ub)
    scales = (x_token_max / qtype_max)[:, None]

    # Quant
    if quant_dtype == torch.int8:
        iscales = as_float32_tensor(s_1 / scales)
        torch_out = as_float32_tensor(x) * iscales
        torch_out = torch_out.round()
        torch_out = torch_out.clamp(qtype_traits_min, qtype_traits_max).to(quant_dtype)
    else:
        assert quant_dtype == FP8_DTYPE
        min_scaling_factor = s_1 / (qtype_max * s_512)
        scales = scales.clamp(min=min_scaling_factor)
        torch_out = as_float32_tensor(x) / scales
        torch_out = torch_out.clamp(qtype_traits_min, qtype_traits_max).to(quant_dtype)

    return torch_out, scales