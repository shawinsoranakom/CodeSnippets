def _is_fp8_w4a8(
        self,
        weight_quant: list[dict[str, Any]] | None,
        input_quant: dict[str, Any] | None,
    ) -> bool:
        # Confirm weights and input quantized.
        if weight_quant is None or input_quant is None:
            return False

        if not isinstance(weight_quant, list) or len(weight_quant) != 2:
            return False

        # Confirm weight scheme is supported
        is_w4a8_dtype = (
            weight_quant[0].get("dtype") == "fp8_e4m3"
            and weight_quant[1].get("dtype") == "int4"
            and input_quant.get("dtype") == "fp8_e4m3"
        )
        is_static_weight = not weight_quant[0].get("is_dynamic") and not weight_quant[
            1
        ].get("is_dynamic")
        is_per_tensor_fp8_and_per_channel_int4_weight = (
            weight_quant[0].get("qscheme") == "per_tensor"
            and weight_quant[1].get("qscheme") == "per_channel"
            and weight_quant[1].get("symmetric") is True
            and weight_quant[1].get("ch_axis") == 0
        )

        if not (
            is_w4a8_dtype
            and is_static_weight
            and is_per_tensor_fp8_and_per_channel_int4_weight
        ):
            return False

        # Dynamic quantization is always supported if weights supported.
        if input_quant.get("is_dynamic"):
            return True

        # Confirm activation scheme is supported.
        is_per_tensor_activation = input_quant.get("qscheme") == "per_tensor"
        return is_per_tensor_activation