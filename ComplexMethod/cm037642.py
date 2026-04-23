def _is_fp8_w4a8(
        weight_quant: QuantizationArgs, input_quant: QuantizationArgs
    ) -> bool:
        if not weight_quant or not input_quant:
            return False
        is_weight_4_bits = weight_quant.num_bits == 4
        is_activation_8_bits = input_quant.num_bits == 8
        weight_strategy = weight_quant.strategy == QuantizationStrategy.GROUP.value
        is_token = (
            weight_strategy and input_quant.strategy == QuantizationStrategy.TOKEN.value
        )
        is_dynamic = not weight_quant.dynamic and input_quant.dynamic
        is_symmetric = weight_quant.symmetric and input_quant.symmetric
        # Only per-group symmetric weight (4bit)
        # + per-tok symmetric activation (8bit) quantization supported.
        return (
            is_weight_4_bits
            and is_activation_8_bits
            and is_token
            and is_symmetric
            and is_dynamic
        )