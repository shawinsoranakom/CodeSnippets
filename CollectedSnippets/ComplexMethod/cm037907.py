def load_weights(self, weights: Iterable[tuple[str, torch.Tensor]]) -> set[str]:
        stacked_params_mapping = [
            # (param_name, shard_name, shard_id)
            ("qkv_proj", "q_proj", "q"),
            ("qkv_proj", "k_proj", "k"),
            ("qkv_proj", "v_proj", "v"),
        ]
        params_dict = dict(self.named_parameters())
        loaded_params: set[str] = set()
        layer_count = len(self.encoder.layers)

        for name, loaded_weight in weights:
            # skip pooling header
            if name.startswith("head."):
                continue

            # post_layernorm is optional
            if name.startswith("post_layernorm.") and not self.require_post_norm:
                continue

            # omit layers when num_hidden_layers_override is set
            if name.startswith("encoder.layers."):
                layer_idx = int(name.split(".")[2])
                if layer_idx >= layer_count:
                    continue

            for param_name, weight_name, shard_id in stacked_params_mapping:
                if weight_name not in name or self.use_data_parallel:
                    continue
                name = name.replace(weight_name, param_name)
                param = params_dict[name]
                weight_loader = param.weight_loader
                weight_loader(param, loaded_weight, shard_id)
                break
            else:
                param = params_dict[name]
                weight_loader = getattr(param, "weight_loader", default_weight_loader)
                weight_loader(param, loaded_weight)
            loaded_params.add(name)
        return loaded_params