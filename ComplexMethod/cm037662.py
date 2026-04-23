def _is_static_tensor_w8a8(
        self,
        weight_quant: dict[str, Any] | None,
        input_quant: dict[str, Any] | None,
    ) -> bool:
        # Confirm weights and input quantized.
        if weight_quant is None or input_quant is None:
            return False

        is_int8_dtype = (
            weight_quant.get("dtype") == "int8" and input_quant.get("dtype") == "int8"
        )

        is_tensor = (
            weight_quant.get("qscheme") in ["per_tensor", "per_channel"]
            and input_quant.get("qscheme") == "per_tensor"
        )

        is_static = not weight_quant.get("is_dynamic") and not input_quant.get(
            "is_dynamic"
        )

        is_weight_symmetric = weight_quant.get("symmetric") is True

        # Both symmetric and asymmetric input quantization supported.
        # Only symmetric weight quantization supported.
        return is_int8_dtype and is_tensor and is_weight_symmetric and is_static