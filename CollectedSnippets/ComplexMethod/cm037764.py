def _get_config_quant_dtype(
    use_fp8_w8a8: bool,
    use_int8_w8a8: bool,
    ocp_mx_scheme: str | None,
) -> None | torch.dtype | str:
    """
    Get the quantization type based on the quantization strategy flags.
    We don't have a quant_config at this point so we need to work backwards.
    A return type of None means no quantization is required because the
    input is unquantized or has been quantized prior to calling
    fused_experts_impl.
    """
    if use_fp8_w8a8:
        return current_platform.fp8_dtype()
    elif use_int8_w8a8:
        return torch.int8
    elif ocp_mx_scheme == "w_mxfp4_a_mxfp4":
        return "mxfp4"
    elif ocp_mx_scheme in {"w_mxfp4_a_mxfp6_e3m2", "w_mxfp6_e3m2_a_mxfp6_e3m2"}:
        return "mxfp6_e3m2"
    elif ocp_mx_scheme in {"w_mxfp4_a_mxfp6_e2m3", "w_mxfp6_e2m3_a_mxfp6_e2m3"}:
        return "mxfp6_e2m3"
    elif ocp_mx_scheme in {"w_mxfp4", "w_mxfp6_e3m2", "w_mxfp6_e2m3"}:
        return torch.bfloat16
    elif ocp_mx_scheme in {"w_mxfp4_a_fp8", "w_mxfp6_e3m2_a_fp8", "w_mxfp6_e2m3_a_fp8"}:
        return torch.float8_e4m3fn

    return None