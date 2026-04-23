def get_quant_method(
        self, layer: torch.nn.Module, prefix: str
    ) -> "QuantizeMethodBase | None":
        # Check if the layer is skipped for quantization.
        exclude_layers = cast(list[str], self.quant_config.get("exclude"))
        if should_ignore_layer(
            prefix, ignore=exclude_layers, fused_mapping=self.packed_modules_mapping
        ):
            if (
                "self_attn" not in prefix  # only quantize attention projections
                or not getattr(self, "dynamic_mxfp4_quant", False)
                or not isinstance(layer, LinearBase)  # Ignore other methods
            ):
                return UnquantizedLinearMethod()

            scheme = self.get_scheme(
                layer=layer,
                layer_name=prefix,
                dynamic_mxfp4_quant=True,
            )
            layer.scheme = scheme
            return QuarkLinearMethod(self)
        if isinstance(layer, LinearBase):
            scheme = self.get_scheme(layer=layer, layer_name=prefix)
            layer.scheme = scheme
            return QuarkLinearMethod(self)
        if isinstance(layer, Attention):
            return QuarkKVCacheMethod(self)

        if isinstance(layer, FusedMoE):
            return QuarkMoEMethod.get_moe_method(self, module=layer, layer_name=prefix)
        return None