def __post_init__(self):
        # support `EngineArgs(compilation_config={...})`
        # without having to manually construct a
        # CompilationConfig object
        if isinstance(self.compilation_config, dict):
            self.compilation_config = CompilationConfig(**self.compilation_config)
        if isinstance(self.attention_config, dict):
            self.attention_config = AttentionConfig(**self.attention_config)
        if isinstance(self.mamba_config, dict):
            self.mamba_config = MambaConfig(**self.mamba_config)
        if isinstance(self.kernel_config, dict):
            self.kernel_config = KernelConfig(**self.kernel_config)
        if isinstance(self.eplb_config, dict):
            self.eplb_config = EPLBConfig(**self.eplb_config)
        if isinstance(self.weight_transfer_config, dict):
            self.weight_transfer_config = WeightTransferConfig(
                **self.weight_transfer_config
            )
        if isinstance(self.ir_op_priority, dict):
            self.ir_op_priority = IrOpPriorityConfig(**self.ir_op_priority)

        from vllm.config.quantization import resolve_online_quant_config

        self.quantization_config = resolve_online_quant_config(
            self.quantization, self.quantization_config
        )

        # Setup plugins
        from vllm.plugins import load_general_plugins

        load_general_plugins()
        # when use hf offline,replace model and tokenizer id to local model path
        if huggingface_hub.constants.HF_HUB_OFFLINE:
            model_id = self.model
            self.model = get_model_path(self.model, self.revision)
            if model_id is not self.model:
                logger.info(
                    "HF_HUB_OFFLINE is True, replace model_id [%s] to model_path [%s]",
                    model_id,
                    self.model,
                )
            if self.tokenizer is not None:
                tokenizer_id = self.tokenizer
                self.tokenizer = get_model_path(self.tokenizer, self.tokenizer_revision)
                if tokenizer_id is not self.tokenizer:
                    logger.info(
                        "HF_HUB_OFFLINE is True, replace tokenizer_id [%s] "
                        "to tokenizer_path [%s]",
                        tokenizer_id,
                        self.tokenizer,
                    )