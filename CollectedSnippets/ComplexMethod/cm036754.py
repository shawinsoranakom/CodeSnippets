def ref_dynamic_per_token_or_block_quant(
    rms_norm_layer: RMSNorm,
    x: torch.Tensor,
    quant_dtype: torch.dtype,
    residual: torch.Tensor | None,
    scale_ub: torch.Tensor | None,
    group_size: list[int] | None,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor | None]:
    if scale_ub is not None:
        assert quant_dtype == current_platform.fp8_dtype()

    # Norm
    torch_out, residual = ref_rms_norm(rms_norm_layer, x, residual)

    # Quant
    if group_size is not None:
        if quant_dtype == current_platform.fp8_dtype():
            torch_out, scales = per_token_group_quant_fp8(
                torch_out, group_size=group_size[1], use_ue8m0=False
            )
        else:
            assert quant_dtype == torch.int8
            torch_out, scales = per_token_group_quant_int8(
                torch_out, group_size=group_size[1]
            )
    else:
        if quant_dtype == current_platform.fp8_dtype():
            torch_out, scales = ops.scaled_fp8_quant(
                torch_out, scale_ub=scale_ub, use_per_token_if_dynamic=True
            )
        else:
            assert quant_dtype == torch.int8
            torch_out, scales, _ = ops.scaled_int8_quant(torch_out)

    return torch_out, scales, residual