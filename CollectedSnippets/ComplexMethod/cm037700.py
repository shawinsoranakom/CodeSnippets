def prepare_nvfp4_moe_layer_for_fi_or_cutlass(
    backend: "NvFp4MoeBackend",
    layer: "FusedMoE",
    w13: torch.Tensor,
    w13_scale: torch.Tensor,
    w13_scale_2: torch.Tensor,
    a13_scale: torch.Tensor,
    w2: torch.Tensor,
    w2_scale: torch.Tensor,
    w2_scale_2: torch.Tensor,
    a2_scale: torch.Tensor,
    is_act_and_mul: bool,
) -> tuple[
    torch.Tensor,
    torch.Tensor,
    torch.Tensor,
    torch.Tensor,
    torch.Tensor,
    torch.Tensor,
    torch.Tensor,
    torch.Tensor,
]:
    # Delayed import for circular dependency avoidance.
    from vllm.model_executor.layers.fused_moe.oracle.nvfp4 import (
        NvFp4MoeBackend,
        is_global_sf_supported_for_nvfp4_backend,
    )

    assert backend in [
        NvFp4MoeBackend.VLLM_CUTLASS,
        NvFp4MoeBackend.FLASHINFER_CUTLASS,
        NvFp4MoeBackend.FLASHINFER_TRTLLM,
        NvFp4MoeBackend.FLASHINFER_CUTEDSL_BATCHED,
    ]

    # Reorder [w1, w3] to [w3, w1] for FI NVFP4 MoE kernels.
    is_gated = layer.activation.is_gated
    if (
        is_gated
        and is_act_and_mul
        and backend
        in [
            NvFp4MoeBackend.FLASHINFER_CUTLASS,
            NvFp4MoeBackend.FLASHINFER_TRTLLM,
        ]
    ):
        w13, w13_scale = reorder_w1w3_to_w3w1(w13, w13_scale)

    # For some FI kernels, the input scales are shared by all experts.
    if is_global_sf_supported_for_nvfp4_backend(backend):
        num_experts = w13.shape[0]
        a13_scale = a13_scale.max().to(torch.float32).expand(num_experts)
        a2_scale = a2_scale.max().to(torch.float32).expand(num_experts)
    else:
        a13_scale = a13_scale.max(dim=1).values.to(torch.float32)

    # Shuffle weights and scales for FI TRTLLM NVFP4 MoE kernels.
    if backend == NvFp4MoeBackend.FLASHINFER_TRTLLM:
        w13, w13_scale, w2, w2_scale, padded_hidden = (
            align_trtllm_fp4_moe_hidden_dim_for_fi(w13, w13_scale, w2, w2_scale)
        )
        if layer.moe_config.hidden_dim_unpadded is None:
            layer.moe_config.hidden_dim_unpadded = layer.moe_config.hidden_dim
        layer.moe_config.hidden_dim = padded_hidden

        # Align weights for FI NVFP4 MoE kernels.
        min_alignment = 16 if is_gated else 128
        w13, w13_scale, w2, w2_scale, padded_intermediate = (
            align_fp4_moe_weights_for_fi(
                w13, w13_scale, w2, w2_scale, is_act_and_mul, min_alignment
            )
        )
        layer.moe_config.intermediate_size_per_partition = padded_intermediate

        w13, w13_scale, w2, w2_scale = prepare_static_weights_for_trtllm_fp4_moe(
            w13,
            w2,
            w13_scale,
            w2_scale,
            hidden_size=w2.size(-2),
            intermediate_size=w13.size(-2) // 2 if is_gated else w13.size(-2),
            num_experts=w13.size(0),
            is_gated_activation=is_gated,
        )
    else:
        # Swizzle the block scales for other FI NVFP4 MoE kernels.
        w13_scale = swizzle_blockscale(w13_scale)

        # Apply padding if needed.
        pad_size = w13_scale.size(1) - w13.size(1)
        if pad_size > 0:
            if is_act_and_mul:
                raise NotImplementedError(
                    "Intermediate size padding for w1 and w3, for %s "
                    "NvFp4 backend, but this is not currently supported",
                    backend.value,
                )
            w13 = torch.nn.functional.pad(w13, (0, 0, 0, pad_size))
            w2 = torch.nn.functional.pad(w2, (0, pad_size // 2, 0, 0))
            w2_scale = torch.nn.functional.pad(w2_scale, (0, pad_size // 16))

        w2_scale = swizzle_blockscale(w2_scale)

    return w13, w13_scale, w13_scale_2, a13_scale, w2, w2_scale, w2_scale_2, a2_scale