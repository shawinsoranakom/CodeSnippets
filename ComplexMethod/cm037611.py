def get_quant_method(self, layer: torch.nn.Module, prefix: str):
        if prefix and self.extra_config:
            for layer_name in self.extra_config:
                if (
                    layer_name == prefix or layer_name == f"model.{prefix}"
                ) and self.extra_config[layer_name].get("bits", 16) >= 16:
                    return UnquantizedLinearMethod()
        if current_platform.is_xpu():
            return self.apply_xpu_w4a16_quant_layer(layer, prefix)
        is_gptq = "gptq" in self.packing_format or "gptq" in self.backend
        if current_platform.is_cpu() and is_gptq:
            return self.apply_cpu_w4a16_quant_layer(layer, prefix)
        if is_gptq:
            return self.apply_gptq_quant_layer(layer, prefix)
        if "awq" in self.packing_format or "awq" in self.backend:
            return self.apply_awq_quant_layer(layer, prefix)

        raise NotImplementedError(
            f"Unsupported quantization configuration for layer '{prefix}'. "
            f"Platform: CPU={current_platform.is_cpu()}. "
            f"Platform: XPU={current_platform.is_xpu()}. "
            f"Format: {self.packing_format}, Backend: {self.backend}."
        )