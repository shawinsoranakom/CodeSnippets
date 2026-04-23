def convert(
        self,
        input_dict: dict[str, torch.Tensor],
        source_patterns: list[str] | None = None,
        model: torch.nn.Module | None = None,
        full_layer_name: str | None = None,
        missing_keys=None,
        **kwargs,
    ) -> dict[str, torch.Tensor]:
        """
        Consolidates tensor subclass components before reconstructing the object

        For example:
            input_dict: {
                "_weight_qdata": torch.Tensor,
                "_weight_scale": torch.Tensor,
            }
            full_layer_name: "model.layers.0.self_attn.k_proj.weight"

            Given this, we reconstruct a Float8Tensor instance using the qdata and scale
            and return it as a dictionary with the full_layer_name as the key and the recovered
            Float8Tensor instance as the value.
        """
        is_unsafe_serialization = list(input_dict.keys())[0] not in source_patterns

        param_data = {}
        layer_name = ".".join(full_layer_name.split(".")[:-1])
        if is_unsafe_serialization:
            if isinstance(input_dict["weight"], list):
                weight = input_dict["weight"][0]
            else:
                weight = input_dict["weight"]
        else:
            for suffix in input_dict.keys():
                if len(input_dict[suffix]) != 1:
                    raise ValueError(
                        f"Expected a single tensor for {suffix} but got {len(input_dict[suffix])} tensors instead"
                    )
                param_data[f"{layer_name}.{suffix}"] = input_dict[suffix][0]

        # If it's unsafe-serialized (i.e. not safetensors), no need for anything
        if is_unsafe_serialization:
            return {full_layer_name: weight}
        elif not is_metadata_torchao(self.hf_quantizer.metadata):
            raise ValueError("Invalid torchao safetensors metadata")

        unflattened_state_dict, leftover_state_dict = unflatten_tensor_state_dict(
            param_data, self.hf_quantizer.metadata
        )
        assert not leftover_state_dict  # there should be no unprocessed tensors
        new_param = unflattened_state_dict[full_layer_name]

        module, _ = get_module_from_name(model, full_layer_name)
        # Add repr to the module
        if isinstance(module, torch.nn.Linear):
            module.extra_repr = types.MethodType(_linear_extra_repr, module)

        return {full_layer_name: new_param}