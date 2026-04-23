def _quantized_4bit_generator(
        self, hf_weights_files, use_safetensors, quant_state_dict
    ) -> Generator:
        from bitsandbytes.functional import QuantState

        # First iterate over all quant state weights
        weight_iterator = self._hf_weight_iter(hf_weights_files, use_safetensors)
        temp_state_dict = {}
        for (
            org_weight_name,
            mapped_weight_name,
            weight_tensor,
        ) in weight_iterator:
            if not self._is_4bit_weight_name(mapped_weight_name):
                continue
            # bitsandbytes library requires
            # weight.quant_state.bitsandbytes__* in CPU
            if "quant_state.bitsandbytes" in mapped_weight_name:
                temp_state_dict[mapped_weight_name] = weight_tensor.cpu().data
            else:
                temp_state_dict[mapped_weight_name] = weight_tensor

        # Closure to parse quant_state for each prequant weight
        def _parse_quant_state(param_name: str, temp_state_dict: dict) -> QuantState:
            quant_state = {}
            for k in temp_state_dict:
                if param_name + "." in k:
                    quant_state[k] = temp_state_dict[k]

            return QuantState.from_dict(
                quant_state, device=current_platform.device_type
            )

        # Second iterate over all prequant and normal weights
        # pre quantized weights would have a quant_state
        for (
            org_weight_name,
            mapped_weight_name,
            weight_tensor,
        ) in self._hf_weight_iter(hf_weights_files, use_safetensors):
            if self._is_4bit_weight_name(mapped_weight_name):
                continue

            if (
                f"{mapped_weight_name}.quant_state.bitsandbytes__nf4" in temp_state_dict
            ) or (
                f"{mapped_weight_name}.quant_state.bitsandbytes__fp4" in temp_state_dict
            ):
                quant_state = _parse_quant_state(mapped_weight_name, temp_state_dict)
                quant_state_dict[mapped_weight_name] = quant_state
                yield org_weight_name, weight_tensor
            else:
                yield org_weight_name, weight_tensor