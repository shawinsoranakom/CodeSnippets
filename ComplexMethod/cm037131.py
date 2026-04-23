def configure(self, config: VllmConfig) -> None:
        self.pass_config = config.compilation_config.pass_config

        # Set the current vllm config to allow tracing CustomOp instances
        with set_current_vllm_config(config, check_compile=False):
            if self.pass_config.eliminate_noops:
                self.passes += [NoOpEliminationPass(config)]

            if self.pass_config.enable_sp:
                self.passes += [SequenceParallelismPass(config)]
                if self.pass_config.fuse_gemm_comms:
                    self.passes += [AsyncTPPass(config)]

            if self.pass_config.fuse_allreduce_rms:
                self.passes += [AllReduceFusionPass(config)]

            if self.pass_config.fuse_minimax_qk_norm:
                self.passes += [MiniMaxQKNormPass(config)]

            if self.pass_config.fuse_norm_quant:
                self.passes += [RMSNormQuantFusionPass(config)]
                if rocm_aiter_ops.is_enabled():
                    self.passes += [
                        RocmAiterRMSNormQuantFusionPass(config),
                    ]
            if self.pass_config.fuse_act_quant:
                self.passes += [ActivationQuantFusionPass(config)]
                if rocm_aiter_ops.is_enabled():
                    self.passes += [RocmAiterSiluMulFp8GroupQuantFusionPass(config)]

            if self.pass_config.fuse_act_padding and rocm_aiter_ops.is_enabled():
                self.passes += [RocmAiterTritonAddRMSNormPadFusionPass(config)]

            if self.pass_config.fuse_mla_dual_rms_norm and rocm_aiter_ops.is_enabled():
                self.passes += [MLADualRMSNormFusionPass(config)]

            if self.pass_config.fuse_rope_kvcache:
                self.passes += [SplitCoalescingPass(config)]
                self.passes += [ScatterSplitReplacementPass(config)]
                self.passes += [RopeKVCacheFusionPass(config)]

            if self.pass_config.fuse_attn_quant:
                self.passes += [AttnQuantFusionPass(config)]
                self.passes += [MLAAttnQuantFusionPass(config)]

            if self.pass_config.enable_qk_norm_rope_fusion:
                self.passes += [SplitCoalescingPass(config)]
                self.passes += [QKNormRoPEFusionPass(config)]

            self.ir_lowering = VllmIRLoweringPass(config)
            self.post_cleanup = PostCleanupPass(config)
            self.fix_functionalization = FixFunctionalizationPass(config)