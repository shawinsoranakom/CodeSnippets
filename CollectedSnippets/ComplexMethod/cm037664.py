def _is_dynamic_per_token_w8a8(
        self,
        weight_quant: dict[str, Any] | None,
        input_quant: dict[str, Any] | None,
    ) -> bool:
        """Detect W8A8 INT8 with per-tensor or per-channel
        weights and dynamic per-token input."""
        if weight_quant is None or input_quant is None:
            return False

        is_int8_dtype = (
            weight_quant.get("dtype") == "int8" and input_quant.get("dtype") == "int8"
        )

        is_valid_weight_scheme = weight_quant.get("qscheme") in [
            "per_tensor",
            "per_channel",
        ]
        is_per_token_input = input_quant.get("qscheme") == "per_channel"

        is_dynamic_input = input_quant.get("is_dynamic") is True
        is_weight_symmetric = weight_quant.get("symmetric") is True

        return (
            is_int8_dtype
            and is_valid_weight_scheme
            and is_per_token_input
            and is_dynamic_input
            and is_weight_symmetric
        )