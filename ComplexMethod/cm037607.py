def get_quant_method(
        self, layer: torch.nn.Module, prefix: str
    ) -> "QuantizeMethodBase | None":
        """Return quantize-method based on layer."""
        # KV-cache quantization
        if isinstance(layer, Attention):
            if self.kv_cache_quant_method:
                return ModelOptFp8KVCacheMethod(self)
            return None

        # Excluded layers
        if self.is_layer_excluded(prefix):
            if isinstance(layer, LinearBase):
                return UnquantizedLinearMethod()
            return None

        quant_algo = self._resolve_quant_algo(prefix)

        if isinstance(layer, LinearBase):
            if quant_algo == "FP8":
                return ModelOptFp8LinearMethod(self.fp8_config)
            if quant_algo == "NVFP4":
                return ModelOptNvFp4LinearMethod(self.nvfp4_config)
            # Layer not in quantized_layers — leave unquantized
            return UnquantizedLinearMethod()

        if isinstance(layer, FusedMoE):
            if quant_algo == "FP8":
                return ModelOptFp8MoEMethod(
                    quant_config=self.fp8_config,
                    moe_config=layer.moe_config,
                )
            if quant_algo == "NVFP4":
                return ModelOptNvFp4FusedMoE(
                    quant_config=self.nvfp4_config,
                    moe_config=layer.moe_config,
                )
            return None

        return None