def load_weights(self, weights: Iterable[tuple[str, torch.Tensor]]) -> set[str]:
        stacked_params_mapping = [
            ("qkv_proj", "q_proj", "q"),
            ("qkv_proj", "k_proj", "k"),
            ("qkv_proj", "v_proj", "v"),
            ("gate_up_proj", "gate_proj", 0),
            ("gate_up_proj", "up_proj", 1),
        ]

        linear_attn_stacked_params_mapping = [
            ("in_proj_qkvg", "q_proj", 0),
            ("in_proj_qkvg", "k_proj", 1),
            ("in_proj_qkvg", "v_proj", 2),
            ("in_proj_qkvg", "g_proj", 3),
            ("conv1d", "q_conv1d", 0),
            ("conv1d", "k_conv1d", 1),
            ("conv1d", "v_conv1d", 2),
        ]

        params_dict = dict(self.named_parameters(remove_duplicate=False))
        loaded_params: set[str] = set()

        for name, loaded_weight in weights:
            if is_pp_missing_parameter(name, self):
                continue

            handled = False

            if "linear_attn" in name:
                for (
                    param_name,
                    weight_name,
                    shard_id,
                ) in linear_attn_stacked_params_mapping:
                    if weight_name not in name:
                        continue
                    mapped_name = name.replace(weight_name, param_name)
                    if mapped_name.endswith(".bias") and (
                        mapped_name not in params_dict
                    ):
                        continue
                    if mapped_name not in params_dict:
                        continue
                    param = params_dict[mapped_name]
                    weight_loader = param.weight_loader
                    weight_loader(param, loaded_weight, shard_id)
                    name = mapped_name
                    handled = True
                    break
            else:
                for param_name, weight_name, shard_id in stacked_params_mapping:
                    if weight_name not in name:
                        continue
                    name = name.replace(weight_name, param_name)
                    if name.endswith(".bias") and name not in params_dict:
                        continue
                    if name not in params_dict:
                        continue
                    param = params_dict[name]
                    weight_loader = param.weight_loader
                    weight_loader(param, loaded_weight, shard_id)
                    handled = True
                    break

            if not handled:
                if name.endswith(".bias") and name not in params_dict:
                    continue
                if name not in params_dict:
                    continue
                param = params_dict[name]
                weight_loader = getattr(param, "weight_loader", default_weight_loader)
                weight_loader(param, loaded_weight)
            loaded_params.add(name)
        return loaded_params