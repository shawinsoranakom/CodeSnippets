def apply_awq_quant_layer(self, layer, prefix: str, backend: str = "auto"):
        from vllm.model_executor.layers.fused_moe import FusedMoE
        from vllm.model_executor.layers.quantization.utils.marlin_utils import (
            check_marlin_supported,
            check_moe_marlin_supports_layer,
        )

        weight_bits, group_size, sym = self.get_layer_config(layer, prefix)
        if not self.check_quantized(weight_bits):
            if isinstance(layer, (LinearBase, ParallelLMHead)):
                return UnquantizedLinearMethod()
            else:
                return None

        logger.debug(
            "[%s] Type: %s, Bits: %s, Group Size: %s, Sym: %s",
            prefix,
            layer.__class__.__name__,
            weight_bits,
            group_size,
            sym,
        )
        if backend == "auto" or "marlin" in backend:
            AWQ_TYPE_MAP = {
                4: scalar_types.uint4,
                8: scalar_types.uint8,
            }
            use_marlin = (weight_bits in AWQ_TYPE_MAP) and check_marlin_supported(
                AWQ_TYPE_MAP[weight_bits], group_size, not sym
            )

            if isinstance(layer, FusedMoE):
                use_marlin = use_marlin and check_moe_marlin_supports_layer(
                    layer, group_size
                )

        else:
            use_marlin = False
        if use_marlin:
            from vllm.model_executor.layers.quantization.awq_marlin import (
                AWQMarlinConfig,
                AWQMarlinLinearMethod,
                AWQMarlinMoEMethod,
            )

            quant_args_marlin = AWQMarlinConfig(
                weight_bits=weight_bits,
                group_size=group_size,
                zero_point=not sym,
                lm_head_quantized=False,
                full_config={},
                modules_to_not_convert=[],
            )
        else:
            from vllm.model_executor.layers.quantization.awq import (
                AWQConfig,
                AWQLinearMethod,
            )

            quant_args = AWQConfig(
                weight_bits=weight_bits,
                group_size=group_size,
                zero_point=not sym,
            )

        if isinstance(layer, FusedMoE):
            if use_marlin:
                return AWQMarlinMoEMethod(quant_args_marlin, layer.moe_config)
            from vllm.model_executor.layers.quantization.moe_wna16 import MoeWNA16Config

            config = {
                "quant_method": "awq",
                "bits": weight_bits,
                "group_size": group_size,
                "zero_point": not sym,
                "lm_head": False,
            }
            return MoeWNA16Config.from_config(config).get_quant_method(layer, prefix)

        if isinstance(layer, (LinearBase, ParallelLMHead)):
            if use_marlin:
                return AWQMarlinLinearMethod(quant_args_marlin)
            else:
                return AWQLinearMethod(quant_args)
        return None