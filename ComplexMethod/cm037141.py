def __init__(self, config: VllmConfig) -> None:
        super().__init__(config, "mla_attn_quant_fusion")

        dtype = config.model_config.dtype
        layers = list(get_layers_from_vllm_config(config, MLAAttention).values())

        if len(layers) == 0:
            logger.warning(
                "MLA attention + quant fusion is enabled, but no MLA "
                "attention layers were found in "
                "CompilationConfig.static_forward_context "
                "so no fusion patterns were registered."
            )

        # When _USE_LAYERNAME is enabled, layer_name is a wildcard so all
        # layers produce the same pattern — register once then break.
        for layer in layers:
            if layer.impl.fused_output_quant_supported(kFp8StaticTensorSym):
                self.register(MLAAttnFp8StaticQuantPattern(layer, dtype))
                if _USE_LAYERNAME:
                    break

        if current_platform.is_cuda() and hasattr(torch.ops._C, "scaled_fp4_quant"):
            for layer in layers:
                if layer.impl.fused_output_quant_supported(kNvfp4Dynamic):
                    self.register(MLAAttnNvfp4QuantPattern(layer, dtype))
                    if _USE_LAYERNAME:
                        break

        # Per-group FP8 (block quant) — register all flag combinations.
        if current_platform.is_cuda():
            for quant_key in [kFp8Dynamic128Sym, kFp8Dynamic64Sym]:
                for col_major in [True, False]:
                    for is_e8m0 in [True, False]:
                        for tma_aligned in [False, True]:
                            for layer in layers:
                                if layer.impl.fused_output_quant_supported(quant_key):
                                    self.register(
                                        MLAAttnFp8GroupQuantPattern(
                                            layer,
                                            dtype,
                                            quant_key,
                                            col_major,
                                            is_e8m0,
                                            tma_aligned,
                                        )
                                    )
                                    if _USE_LAYERNAME:
                                        break

        self.dump_patterns(config, self.pm_pass)