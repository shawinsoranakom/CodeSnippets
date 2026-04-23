def __init__(self, config: VllmConfig) -> None:
        super().__init__(config, "attn_quant_fusion")

        dtype = config.model_config.dtype
        layers = list(get_layers_from_vllm_config(config, Attention).values())

        if len(layers) == 0:
            logger.warning(
                "Attention + quant fusion is enabled, but no attention layers "
                "were found in CompilationConfig.static_forward_context "
                "so no fusion patterns were registered."
            )

        # When _USE_LAYERNAME is enabled, layer_name is a wildcard so all
        # layers produce the same pattern — register once then break.
        for layer in layers:
            if layer.impl.fused_output_quant_supported(_FP8_QUANT_KEY):
                self.register(AttnFp8StaticQuantPattern(layer, dtype))
                if _USE_LAYERNAME:
                    break

        if current_platform.is_cuda() and hasattr(torch.ops._C, "scaled_fp4_quant"):
            for layer in layers:
                if layer.impl.fused_output_quant_supported(kNvfp4Dynamic):
                    self.register(AttnNvfp4QuantPattern(layer, dtype))
                    if _USE_LAYERNAME:
                        break

        self.dump_patterns(config, self.pm_pass)