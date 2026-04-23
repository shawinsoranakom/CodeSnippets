def load_weights(self, weights: Iterable[tuple[str, torch.Tensor]]) -> set[str]:
        stacked_params_mapping = [
            (".qkv_proj", ".q_proj", "q"),
            (".qkv_proj", ".k_proj", "k"),
            (".qkv_proj", ".v_proj", "v"),
            (".w13", ".w1", 0),
            (".w13", ".w3", 1),
        ]
        params_dict = dict(self.named_parameters())
        loaded_params: set[str] = set()
        for name, loaded_weight in weights:
            if ".conv." in name:
                name = name.replace(".conv.", ".short_conv.", 1)

            for param_name, weight_name, shard_id in stacked_params_mapping:
                # Use segment-boundary matching (trailing dot) to prevent
                # e.g. ".w1" from matching inside ".w13" in pre-fused keys.
                if weight_name + "." not in name:
                    continue
                name = name.replace(weight_name + ".", param_name + ".")

                if is_pp_missing_parameter(name, self):
                    continue
                param = params_dict[name]
                weight_loader = param.weight_loader
                weight_loader(param, loaded_weight, shard_id)
                break
            else:
                if is_pp_missing_parameter(name, self):
                    continue
                param = params_dict[name]
                weight_loader = getattr(param, "weight_loader", default_weight_loader)
                weight_loader(param, loaded_weight)
            loaded_params.add(name)
        return loaded_params