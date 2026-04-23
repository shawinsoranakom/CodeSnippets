def moe_quantize_weights_2d(
    w: torch.Tensor,
    w_s: torch.Tensor | None,
    quant_dtype: torch.dtype | str | None,
    per_token_quant: bool,
    block_shape: list[int] | None,
) -> tuple[torch.Tensor, torch.Tensor | None, torch.Tensor | None]:
    assert (
        quant_dtype == torch.float8_e4m3fn
        or quant_dtype == torch.int8
        or quant_dtype == "nvfp4"
    ), "only fp8/int8/nvfp4 supported"

    w_gs = None

    if block_shape is not None:
        assert not per_token_quant
        if quant_dtype == torch.int8:
            w, w_s = per_block_cast_to_int8(w, block_shape)
        elif quant_dtype == torch.float8_e4m3fn:
            w, w_s = per_block_cast_to_fp8(w, block_shape)
        elif quant_dtype == "nvfp4":
            raise RuntimeError("blocked quantization not supported for nvfp4")
        else:
            raise RuntimeError(f"Unsupported quant type {quant_dtype}")
    else:
        if quant_dtype == torch.int8:
            w, w_s = ops.scaled_int8_quant(
                w, w_s, use_per_token_if_dynamic=per_token_quant
            )
        elif quant_dtype == torch.float8_e4m3fn:
            w, w_s = ops.scaled_fp8_quant(
                w, w_s, use_per_token_if_dynamic=per_token_quant
            )
        elif quant_dtype == "nvfp4":
            assert not per_token_quant
            w_amax = torch.abs(w).max().to(torch.float32)
            w_gs = FLOAT8_E4M3_MAX * FLOAT4_E2M1_MAX / w_amax
            w, w_s = ops.scaled_fp4_quant(w, w_gs)
        else:
            raise RuntimeError(f"Unsupported quant type {quant_dtype}")

    return w, w_s, w_gs