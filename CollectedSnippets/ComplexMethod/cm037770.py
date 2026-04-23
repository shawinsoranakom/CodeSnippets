def moe_kernel_quantize_input(
    A: torch.Tensor,
    A_scale: torch.Tensor | None,
    quant_dtype: None | torch.dtype | str,
    per_act_token_quant: bool,
    block_shape: list[int] | None = None,
    is_fp4_scale_swizzled: bool = True,
    ocp_mx_scheme: str | None = None,
    quantization_emulation: bool = False,
) -> tuple[torch.Tensor, torch.Tensor | None]:
    # Handle OCP MX scheme that requires QDQ (quantize-dequantize) for emulation
    if ocp_mx_scheme is not None:
        if ocp_mx_scheme in {"w_mxfp4", "w_mxfp4_a_mxfp4"}:
            pass  # No QDQ needed for these schemes
        elif ocp_mx_scheme.endswith("a_fp8"):
            # Perform QDQ (quantize and dequantize) on activation for emulation
            # purpose, because there is no native kernel for weight in ocp_mx_scheme
            # and activation in FP8. The implementation is based on existing
            # non-emulation ops.
            qA, qA_scale = ops.scaled_fp8_quant(
                A, A_scale, use_per_token_if_dynamic=False
            )
            A = per_tensor_dequantize(qA, qA_scale).to(A.dtype)
            # After QDQ, we don't need further quantization
            return A, None
        # else: For other schemes (e.g., *_a_mxfp6_e3m2, *_a_mxfp6_e2m3),
        # weights are already dequantized, and we proceed with normal
        # activation quantization below.

    if quant_dtype == current_platform.fp8_dtype():
        if quantization_emulation:
            raise NotImplementedError(
                f"moe_kernel_quantize_input does not support quant_dtype={quant_dtype}"
                " MOE quantization emulation. Please open an issue."
            )
        return _fp8_quantize(A, A_scale, per_act_token_quant, block_shape)
    elif quant_dtype == torch.int8:
        if quantization_emulation:
            raise NotImplementedError(
                "moe_kernel_quantize_input does not support quant_dtype=torch.int8"
                " MOE quantization emulation. Please open an issue."
            )
        return _int8_quantize(A, A_scale, per_act_token_quant, block_shape)
    elif quant_dtype == "nvfp4":
        if not quantization_emulation:
            return _nvfp4_quantize(
                A, A_scale, is_sf_swizzled_layout=is_fp4_scale_swizzled
            )
        else:
            return ref_nvfp4_quant_dequant(A, A_scale, block_size=16)
    elif quant_dtype == "mxfp4":
        if not quantization_emulation:
            raise NotImplementedError(
                "moe_kernel_quantize_input should not be used for native"
                " quant_dtype='mxfp4' MOE. Please open an issue."
            )
        return _mxfp4_quantize(A, A_scale, per_act_token_quant, block_shape)
    elif quant_dtype == "mxfp8":
        # TODO: `quant_dtype == "mxfp8"` is ambiguous,
        # should be fp8_e4m3. OCP MX also defines `fp8_e5m2`.
        if quantization_emulation:
            raise NotImplementedError(
                "moe_kernel_quantize_input does not support quant_dtype='mxfp8' MOE "
                "quantization emulation. Please open an issue."
            )
        return _mxfp8_e4m3_quantize(
            A,
            A_scale,
            per_act_token_quant,
            block_shape,
            is_sf_swizzled_layout=is_fp4_scale_swizzled,
        )
    elif quant_dtype == "mxfp6_e3m2":
        if not quantization_emulation:
            raise NotImplementedError(
                "moe_kernel_quantize_input should not be used for native "
                " quant_dtype='mxfp6_e3m2'MOE. Please open an issue."
            )

        return _mxfp6_e3m2_quantize(A, A_scale, per_act_token_quant, block_shape)
    elif quant_dtype == "mxfp6_e2m3":
        if not quantization_emulation:
            raise NotImplementedError(
                "moe_kernel_quantize_input should not be used for native"
                " quant_dtype='mxfp6_e2m3' MOE. Please open an issue."
            )

        return _mxfp6_e2m3_quantize(A, A_scale, per_act_token_quant, block_shape)
    else:
        return A, A_scale