def convert(
        self,
        input_dict: dict[str, list[torch.Tensor]],
        model: torch.nn.Module | None = None,
        full_layer_name: str | None = None,
        **kwargs,
    ) -> dict[str, torch.Tensor]:
        for key, value in input_dict.items():
            if isinstance(value, list):
                input_dict[key] = value[0]
        key_weight = "weight"
        weight = input_dict.pop(key_weight)
        from ..quantizers.quantizers_utils import get_module_from_name

        needs_unpacking = False
        target_dtype = weight.dtype
        if model is not None and full_layer_name is not None:
            module, _ = get_module_from_name(model, full_layer_name)
            if hasattr(module, "out_features") and hasattr(module, "in_features"):
                # Packed: shape[0] * VALUES_PER_ITEM == out_features
                # Unpacked: shape[0] == out_features
                expected_out = module.out_features
                actual_out = weight.shape[0]
                if actual_out * VALUES_PER_ITEM == expected_out:
                    needs_unpacking = True
        if needs_unpacking:
            weight_uint8 = weight.to(torch.uint8)
            weight = unpack_weights(weight_uint8, dtype=target_dtype)
        return {key_weight: weight}