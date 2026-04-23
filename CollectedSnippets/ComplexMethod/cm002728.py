def process(self, weights, name: str, **kwargs):
        # 1. Handle separate MoE expert tensors (down, gate, up)
        if m := self.GGUF_MOE_WEIGHTS_PATTERN.match(name):
            tensor_key_mapping = kwargs.get("tensor_key_mapping")
            parsed_parameters = kwargs.get("parsed_parameters")
            if tensor_key_mapping and parsed_parameters:
                self._split_moe_expert_tensor(weights, parsed_parameters, m["bid"], m["proj"], tensor_key_mapping)
                return GGUFTensor(weights, None, {})  # signal handled

        # 2. Handle combined gate+up tensor
        if m := self.GGUF_MOE_COMBINED_PATTERN.match(name):
            tensor_key_mapping = kwargs.get("tensor_key_mapping")
            parsed_parameters = kwargs.get("parsed_parameters")
            if tensor_key_mapping and parsed_parameters:
                self._interleave_gate_up_tensor(weights, parsed_parameters, m["bid"], tensor_key_mapping)
                return GGUFTensor(weights, None, {})

        # 3. Bias tensors (1D) → no transpose
        if ".bias" in name and len(weights.shape) == 1:
            return GGUFTensor(weights, name, {})

        # 4. Default handling for all other tensors
        return GGUFTensor(weights, name, {})