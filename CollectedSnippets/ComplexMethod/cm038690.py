def __post_init__(self) -> None:
        # Handle deprecation and defaults

        if not self.eliminate_noops:
            if self.fuse_norm_quant or self.fuse_act_quant:
                logger.warning_once(
                    "Fusion enabled but reshape elimination disabled. "
                    "RMSNorm/SiluMul + quant (fp8) fusion might not work"
                )
            if self.fuse_attn_quant:
                logger.warning_once(
                    "Fusion enabled but reshape elimination disabled. "
                    "Attention + quant (fp8) fusion might not work"
                )
            if self.fuse_allreduce_rms:
                logger.warning_once(
                    "Fusion enabled but reshape elimination disabled. "
                    "Allreduce + rms norm + quant (fp8) fusion might not work"
                )
            if self.fuse_act_padding:
                logger.warning_once(
                    "Fusion enabled but reshape elimination disabled. "
                    "RMSNorm + padding fusion might not work"
                )
        if self.enable_qk_norm_rope_fusion and not current_platform.is_cuda_alike():
            logger.warning_once(
                "QK Norm + RoPE fusion enabled but the current platform is not "
                "CUDA or ROCm. The fusion will be disabled."
            )
            self.enable_qk_norm_rope_fusion = False
        if self.fuse_act_padding and not current_platform.is_rocm():
            logger.warning_once(
                "Padding fusion enabled but the current platform is not ROCm. "
                "The fusion will be disabled."
            )
            self.fuse_act_padding = False
        if self.fuse_mla_dual_rms_norm and not current_platform.is_rocm():
            logger.warning_once(
                "MLA dual RMS norm fusion requires ROCm/AITER. "
                "The fusion will be disabled."
            )
            self.fuse_mla_dual_rms_norm = False
        if self.fuse_rope_kvcache and not current_platform.is_rocm():
            logger.warning_once(
                "KV cache fusion currently only enabled on ROCm. "
                "The fusion will be disabled."
            )
            self.fuse_rope_kvcache = False