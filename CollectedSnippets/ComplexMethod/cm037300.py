def parse(self, args: ParsedArgs, vllm_config: VllmConfig) -> ParsedArgs:
        cfg = vllm_config.model_config.hf_config
        if hasattr(cfg, "text_config") and cfg.text_config is not None:
            cfg = cfg.text_config

        if hasattr(cfg, "moe_layer_freq") and hasattr(cfg, "first_k_dense_replace"):
            args.num_moe_layers = len(
                [
                    layer
                    for layer in range(args.num_hidden_layers)
                    if layer >= cfg.first_k_dense_replace
                    and layer % cfg.moe_layer_freq == 0
                ]
            )

        return args