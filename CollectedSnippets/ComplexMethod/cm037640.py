def _is_dynamic_token_w4a8_int(
        weight_quant: QuantizationArgs, input_quant: QuantizationArgs
    ) -> bool:
        is_weight_4_bits = weight_quant.num_bits == 4
        is_activation_8_bits = input_quant.num_bits == 8
        weight_strategy = (
            weight_quant.strategy == QuantizationStrategy.GROUP.value
            or weight_quant.strategy == QuantizationStrategy.CHANNEL.value
        )
        is_token = (
            weight_strategy and input_quant.strategy == QuantizationStrategy.TOKEN.value
        )
        is_dynamic = not weight_quant.dynamic and input_quant.dynamic

        # Both symmetric and asymmetric input quantization supported.
        # Only symmetric weight quantization supported.
        return (
            is_weight_4_bits
            and is_activation_8_bits
            and is_token
            and weight_quant.symmetric
            and is_dynamic
        )