def _rewrite_spec_layer_name(
        self, spec_layer: int, name: str, new_to_old_names_mapping: dict
    ) -> str:
        """
        Rewrite the weight name to match the format of the original model.
        Add .mtp_block for modules in transformer layer block for spec layer
        and rename shared layer weights to be top level.
        """
        if name in new_to_old_names_mapping:
            name = new_to_old_names_mapping[name]
        spec_layer_weight_names = [
            "embed_tokens",
            "enorm",
            "hnorm",
            "eh_proj",
            "shared_head",
        ]
        if (
            name.startswith("enorm")
            or name.startswith("hnorm")
            or name.startswith("eh_proj")
            or name.startswith("final_layernorm")
        ):
            name = "model.layers." + str(spec_layer) + "." + name
        shared_weight_names = ["embed_tokens"]
        spec_layer_weight = False
        shared_weight = False
        for weight_name in spec_layer_weight_names:
            if weight_name in name:
                spec_layer_weight = True
                if weight_name in shared_weight_names:
                    shared_weight = True
                break
        if not spec_layer_weight:
            # treat rest weights as weights for transformer layer block
            name = name.replace(
                "model.layers.0.", f"model.layers.{spec_layer}.mtp_block."
            )
        elif shared_weight:
            # treat shared weights as top level weights
            name = name.replace("model.layers.0.", "model.")
        return name