def get_quant_method(
        self, layer: torch.nn.Module, prefix: str
    ) -> "QuantizeMethodBase | None":
        if isinstance(layer, LinearBase) or (
            isinstance(layer, ParallelLMHead) and self.lm_head_quantized
        ):
            if is_layer_skipped(
                prefix,
                self.modules_to_not_convert,
                self.packed_modules_mapping,
                skip_with_substr=True,
            ):
                return UnquantizedLinearMethod()
            # Check if the layer is supported by AWQMarlin.
            if not check_marlin_supports_layer(layer, self.group_size):
                logger.warning_once(
                    "Layer '%s' is not supported by AWQMarlin. Falling back to unoptimized AWQ kernels.",  # noqa: E501
                    prefix,
                )
                return AWQConfig.from_config(self.full_config).get_quant_method(
                    layer, prefix
                )
            quant_method = AWQMarlinLinearMethod(self)
            quant_method.input_dtype = get_marlin_input_dtype(prefix)
            return quant_method
        elif isinstance(layer, FusedMoE):
            from vllm.model_executor.layers.quantization.moe_wna16 import MoeWNA16Config

            if is_layer_skipped(
                prefix,
                getattr(self, "modules_to_not_convert", []),
                skip_with_substr=True,
            ):
                return UnquantizedFusedMoEMethod(layer.moe_config)
            if not check_moe_marlin_supports_layer(layer, self.group_size):
                logger.warning_once(
                    f"Layer '{prefix}' is not supported by AWQMoeMarlin. "
                    "Falling back to Moe WNA16 kernels."
                )
                return MoeWNA16Config.from_config(self.full_config).get_quant_method(
                    layer, prefix
                )
            moe_quant_method = AWQMarlinMoEMethod(self, layer.moe_config)
            moe_quant_method.input_dtype = get_marlin_input_dtype(prefix)
            return moe_quant_method
        return None