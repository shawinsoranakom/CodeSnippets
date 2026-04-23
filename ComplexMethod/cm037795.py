def rocm_aiter_fused_experts(
    hidden_states: torch.Tensor,
    w1: torch.Tensor,
    w2: torch.Tensor,
    topk_weights: torch.Tensor,
    topk_ids: torch.Tensor,
    moe_config: FusedMoEConfig,
    activation: MoEActivation = MoEActivation.SILU,
    apply_router_weight_on_input: bool = False,
    expert_map: torch.Tensor | None = None,
    quant_config: FusedMoEQuantConfig | None = None,
    a1q_scale: torch.Tensor | None = None,
    num_local_tokens: torch.Tensor | None = None,
    output_dtype: torch.dtype | None = None,
) -> torch.Tensor:
    """ROCm AITER fused MoE expert computation."""
    if quant_config is None:
        quant_config = FUSED_MOE_UNQUANTIZED_CONFIG

    if activation == MoEActivation.SILU:
        activation_method = ActivationMethod.SILU
    elif activation == MoEActivation.GELU:
        activation_method = ActivationMethod.GELU
    elif activation == MoEActivation.SWIGLUOAI:
        activation_method = rocm_aiter_ops.get_aiter_activation_type("swiglu")
    else:
        raise ValueError(f"Unsupported activation: {activation}")

    # All AITER Fused MoE kernels are expecting the following datatypes
    topk_weights = topk_weights.to(torch.float32)
    topk_ids = topk_ids.to(torch.int32)

    expert_mask = expert_map if expert_map is not None else None

    # w8a8 per-channel quantization
    if (
        quant_config.per_act_token_quant
        and apply_router_weight_on_input
        and quant_config.use_fp8_w8a8
    ):
        # AITER tkw1 kernel for FP8 models with `apply_router_weight_on_input`
        # This applies topk_weights on the GEMM output of the first FC layer
        #  rather than the second FC.
        assert topk_weights.dim() == 2, (
            "`topk_weights` should be in shape (num_tokens, topk)"
        )
        assert topk_weights.shape[-1] == 1, (
            "Only support topk=1 when `apply_router_weight_on_input` is True"
        )
        assert num_local_tokens is None, (
            "AITER tkw1 kernel does not support `num_local_tokens`"
        )

        return rocm_aiter_ops.asm_moe_tkw1(
            hidden_states,
            w1,
            w2,
            topk_weights,
            topk_ids,
            fc1_scale=quant_config.w1_scale,
            fc2_scale=quant_config.w2_scale,
            fc1_smooth_scale=None,
            fc2_smooth_scale=None,
            a16=False,
            per_tensor_quant_scale=None,
            expert_mask=expert_mask,
            activation_method=activation_method,
        )

    else:
        quant_method = QuantMethod.NO.value
        # mxfp4: both w4a4 (quark) and w4a16 (oracle CK) use BLOCK_1X32
        if quant_config.use_mxfp4_w4a4 or quant_config.use_mxfp4_w4a16:
            quant_method = QuantMethod.BLOCK_1X32.value
        # w8a8 block-scaled
        if quant_config.block_shape is not None and quant_config.use_fp8_w8a8:
            assert not apply_router_weight_on_input, (
                "apply_router_weight_on_input is not supported for block scaled moe"
            )
            assert quant_config.w1_scale is not None
            assert quant_config.w2_scale is not None
            quant_method = QuantMethod.BLOCK_128x128.value
        elif quant_config.use_fp8_w8a8 and quant_config.per_out_ch_quant:
            quant_method = QuantMethod.PER_TOKEN.value
        elif quant_config.use_fp8_w8a8:
            # Currently only per tensor quantization method is enabled.
            quant_method = QuantMethod.PER_TENSOR.value

        if apply_router_weight_on_input:
            assert topk_weights.dim() == 2, (
                "`topk_weights` should be in shape (num_tokens, topk)"
            )
            _, topk = topk_weights.shape
            assert topk == 1, (
                "Only support topk=1 when `apply_router_weight_on_input` is True"
            )

        # Compute padding on-the-fly for CK MXFP4 kernels
        hidden_pad = 0
        intermediate_pad = 0
        assert moe_config.hidden_dim_unpadded is not None
        assert moe_config.intermediate_size_per_partition_unpadded is not None
        hidden_pad = hidden_states.shape[1] - moe_config.hidden_dim_unpadded
        intermediate_pad = (
            moe_config.intermediate_size_per_partition
            - moe_config.intermediate_size_per_partition_unpadded
        )

        return rocm_aiter_ops.fused_moe(
            hidden_states,
            w1,
            w2,
            topk_weights,
            topk_ids,
            expert_mask=expert_mask,
            quant_method=quant_method,
            activation_method=activation_method,
            w1_scale=quant_config.w1_scale,
            w2_scale=quant_config.w2_scale,
            a1_scale=quant_config.a1_scale if a1q_scale is None else a1q_scale,
            a2_scale=quant_config.a2_scale,
            doweight_stage1=apply_router_weight_on_input,
            num_local_tokens=num_local_tokens,
            output_dtype=output_dtype,
            hidden_pad=hidden_pad,
            intermediate_pad=intermediate_pad,
            bias1=quant_config.w1_bias if quant_config.use_mxfp4_w4a16 else None,
            bias2=quant_config.w2_bias if quant_config.use_mxfp4_w4a16 else None,
        )