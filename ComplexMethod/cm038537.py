def init_quick_all_reduce(self):
        # On RocM, bfloat16 kernels are slower than fp16
        # due to slower match operations
        # If environment variable is set to 1, we convert input to fp16
        self.use_fp16_kernels = envs.VLLM_ROCM_QUICK_REDUCE_CAST_BF16_TO_FP16
        regime_str = envs.VLLM_ROCM_QUICK_REDUCE_QUANTIZATION
        if regime_str not in QuickReduceRegime.__members__:
            logger.warning(
                "Custom quick allreduce:",
                f"Invalid quantization level: {regime_str}. "
                "Supported levels: "
                f"{list(QuickReduceRegime.__members__.keys())}",
            )
            return

        if regime_str == "NONE":
            logger.debug(
                "Custom quick allreduce is disabled based "
                "on env variable "
                "VLLM_ROCM_QUICK_REDUCE_QUANTIZATION='NONE'"
            )
            return
        self.qr_quant_level = QuickReduceRegime[regime_str]
        vllm_config = get_current_vllm_config_or_none()
        if (
            vllm_config is not None
            and hasattr(vllm_config, "model_config")
            and hasattr(vllm_config.model_config, "dtype")
        ):
            dtype = vllm_config.model_config.dtype
            if dtype not in [torch.float16, torch.bfloat16]:
                logger.debug(
                    "Custom quick allreduce disabled: only supports "
                    "float16 and float16, but get %s.",
                    dtype,
                )
                return

            if dtype == torch.bfloat16 and self.use_fp16_kernels:
                logger.info(
                    "Custom quick allreduce: BF16 inputs will be converted "
                    "to FP16 to improve performance. set "
                    "envs.VLLM_ROCM_QUICK_REDUCE_CAST_BF16_TO_FP16=0 "
                    "to turn off."
                )

        # VLLM_ROCM_QUICK_REDUCE_MAX_SIZE_BYTES_MB is specified in MB
        qr_max_size = envs.VLLM_ROCM_QUICK_REDUCE_MAX_SIZE_BYTES_MB
        if qr_max_size is not None:
            if qr_max_size < 1:
                logger.info(
                    "You should not set a max_size smaller than 1MB, which can "
                    "lead to error or degradation to custom allreduce or rccl."
                )
            qr_max_size = qr_max_size * MB
        self._ptr = ops.init_custom_qr(self.rank, self.world_size, qr_max_size)
        self.qr_max_size = qr_max_size if qr_max_size is not None else ops.qr_max_size()
        self.create_shared_buffer()
        self.disabled = False