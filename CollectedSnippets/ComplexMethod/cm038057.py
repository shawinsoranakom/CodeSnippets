def load_weights(self, weights: Iterable[tuple[str, torch.Tensor]]) -> set[str]:
        stacked_params_mapping = [
            # (param_name, shard_name, shard_id)
            ("qkv_proj", "q_proj", "q"),
            ("qkv_proj", "k_proj", "k"),
            ("qkv_proj", "v_proj", "v"),
        ]
        params_dict = dict(self.named_parameters())
        loaded_params: set[str] = set()
        layer_count = len(self.vision_model.encoder.layers)

        for name, loaded_weight in weights:
            # post_layernorm is optional in SiglipVisionModel
            if (
                name.startswith("vision_model.post_layernorm")
                and self.vision_model.post_layernorm is None
            ):
                continue

            # if the model configuration is not going to use
            # the pooling head for inference, don't load its weights
            if self.vision_model.head is None and name.startswith("vision_model.head"):
                continue

            # omit layers when num_hidden_layers_override is set
            if name.startswith("vision_model.encoder.layers"):
                layer_idx = int(name.split(".")[3])
                if layer_idx >= layer_count:
                    continue

            # Check if this is a scale parameter that needs remapping first
            if name.endswith((".k_scale", ".v_scale", ".q_scale", ".prob_scale")):
                # Try to remap the scale name first
                remapped_name = maybe_remap_kv_scale_name(name, params_dict)
                if remapped_name is not None and remapped_name in params_dict:
                    # Successfully remapped, use the remapped name
                    param = params_dict[remapped_name]
                    weight_loader = getattr(
                        param, "weight_loader", default_weight_loader
                    )
                    weight_loader(param, loaded_weight)
                    loaded_params.add(remapped_name)
                    continue
                # If remapping failed, continue with normal processing

            for param_name, weight_name, shard_id in stacked_params_mapping:
                if weight_name not in name:
                    continue
                name = name.replace(weight_name, param_name)

                param = params_dict[name]
                weight_loader = param.weight_loader
                weight_loader(param, loaded_weight, shard_id)
                break
            else:
                param = params_dict[name]
                param = maybe_swap_ffn_param(
                    name, param, loaded_weight, params_dict, self.quant_config
                )
                weight_loader = getattr(param, "weight_loader", default_weight_loader)
                weight_loader(param, loaded_weight)
            loaded_params.add(name)
        return loaded_params