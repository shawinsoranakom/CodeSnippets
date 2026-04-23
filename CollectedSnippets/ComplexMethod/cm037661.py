def _is_fp8_w8a8(
        self,
        weight_quant: dict[str, Any] | None,
        input_quant: dict[str, Any] | None,
    ) -> bool:
        # Confirm weights and input quantized.
        if weight_quant is None or input_quant is None:
            return False

        # Confirm weight scheme is supported
        is_fp8_dtype = (
            weight_quant.get("dtype") == "fp8_e4m3"
            and input_quant.get("dtype") == "fp8_e4m3"
        )
        is_static_weight = not weight_quant.get("is_dynamic")
        is_per_tensor_or_channel_weight = weight_quant.get("qscheme") in [
            "per_tensor",
            "per_channel",
        ]

        if not (is_fp8_dtype and is_static_weight and is_per_tensor_or_channel_weight):
            return False

        # Dynamic quantization is always supported if weights supported.
        if input_quant.get("is_dynamic"):
            return True

        # Confirm activation scheme is supported.
        is_per_tensor_activation = input_quant.get("qscheme") == "per_tensor"
        return is_per_tensor_activation