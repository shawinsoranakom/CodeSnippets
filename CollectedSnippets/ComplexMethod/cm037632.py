def get_quant_method(
        self, layer: torch.nn.Module, prefix: str
    ) -> "QuantizeMethodBase | None":
        if is_layer_skipped_quant(prefix, self.modules_to_not_convert):
            if isinstance(layer, FusedMoE):
                return UnquantizedFusedMoEMethod(layer.moe_config)
            return UnquantizedLinearMethod()
        elif isinstance(layer, LinearBase):
            # Avoid circular import
            from vllm.model_executor.layers.quantization.awq import AWQConfig
            from vllm.model_executor.layers.quantization.awq_marlin import (
                AWQMarlinConfig,
            )
            from vllm.model_executor.layers.quantization.gptq import GPTQConfig
            from vllm.model_executor.layers.quantization.gptq_marlin import (
                GPTQMarlinConfig,
            )

            if self.linear_quant_method == "gptq":
                if self.use_marlin:
                    return GPTQMarlinConfig.from_config(
                        self.full_config
                    ).get_quant_method(layer, prefix)
                else:
                    return GPTQConfig.from_config(self.full_config).get_quant_method(
                        layer, prefix
                    )
            elif self.linear_quant_method in ("awq", "awq_marlin"):
                if self.use_marlin and check_marlin_supports_layer(
                    layer, self.group_size
                ):
                    return AWQMarlinConfig.from_config(
                        self.full_config
                    ).get_quant_method(layer, prefix)
                else:
                    return AWQConfig.from_config(self.full_config).get_quant_method(
                        layer, prefix
                    )
            else:
                raise ValueError("moe_wna16 only support gptq and awq.")
        elif isinstance(layer, FusedMoE):
            return MoeWNA16Method(self, layer.moe_config)
        return None