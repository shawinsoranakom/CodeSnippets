def get_quant_method(
        self, layer: torch.nn.Module, prefix: str
    ) -> "QuantizeMethodBase | None":
        if isinstance(layer, LinearBase):
            if should_ignore_layer(
                prefix,
                ignore=self.ignored_layers,
                fused_mapping=self.packed_modules_mapping,
            ):
                return UnquantizedLinearMethod()

            linear_scheme = self.args.linear_scheme_override or self.args.global_scheme
            if linear_scheme == OnlineQuantScheme.INT8_PER_CHANNEL_WEIGHT_ONLY:
                logger.warning_once(
                    "INT8 online quantization only quantizes MoE expert "
                    "weights. linear layers remain in full precision."
                )
                return UnquantizedLinearMethod()
            elif linear_scheme == OnlineQuantScheme.FP8_PER_BLOCK:
                return Fp8PerBlockOnlineLinearMethod()
            elif linear_scheme == OnlineQuantScheme.MXFP8:
                return Mxfp8OnlineLinearMethod()
            else:
                return Fp8PerTensorOnlineLinearMethod()
        elif isinstance(layer, FusedMoE):
            if should_ignore_layer(
                prefix,
                ignore=self.ignored_layers,
                fused_mapping=self.packed_modules_mapping,
            ):
                return UnquantizedFusedMoEMethod(layer.moe_config)

            moe_scheme = self.args.moe_scheme_override or self.args.global_scheme
            if moe_scheme == OnlineQuantScheme.INT8_PER_CHANNEL_WEIGHT_ONLY:
                return Int8OnlineMoEMethod(layer=layer)
            elif moe_scheme == OnlineQuantScheme.FP8_PER_BLOCK:
                return Fp8PerBlockOnlineMoEMethod(layer=layer)
            elif moe_scheme == OnlineQuantScheme.MXFP8:
                return Mxfp8OnlineMoEMethod(layer=layer)
            else:
                return Fp8PerTensorOnlineMoEMethod(layer=layer)
        return None