def _fused_moe_grouped_gemm_may_use_deep_gemm(module: torch.nn.Module) -> bool:
    if not (envs.VLLM_USE_DEEP_GEMM and envs.VLLM_MOE_USE_DEEP_GEMM):
        return False

    if not isinstance(module, FusedMoE):
        return False

    moe_quant_config = module.quant_method.get_fused_moe_quant_config(module)

    if (
        moe_quant_config is None
        or moe_quant_config.quant_dtype != torch.float8_e4m3fn
        or moe_quant_config.block_shape != get_mk_alignment_for_contiguous_layout()
    ):
        return False

    moe_kernel = getattr(module.quant_method, "moe_kernel", None)
    if moe_kernel is None:
        return False

    fused_experts = moe_kernel.impl.fused_experts
    return isinstance(fused_experts, (DeepGemmExperts, TritonOrDeepGemmExperts))