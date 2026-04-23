def load_weights(self, weights: Iterable[tuple[str, torch.Tensor]]) -> set[str]:
        stacked_params_mapping = [
            ("gate_up_proj", "gate_proj", 0),
            ("gate_up_proj", "up_proj", 1),
        ]
        params_dict = dict(self.named_parameters())
        loaded_params: set[str] = set()
        total_num_heads = self.config.n_head
        head_dim = self.config.hidden_size // total_num_heads
        for name, loaded_weight in weights:
            if "self_attn.key_value" in name:
                k_weight = []
                v_weight = []
                for i in range(total_num_heads):
                    start = i * head_dim * 2
                    k_weight.append(loaded_weight[start : start + head_dim, :])
                    v_weight.append(
                        loaded_weight[start + head_dim : start + 2 * head_dim :]
                    )
                k_weight = torch.cat(k_weight, dim=0)
                v_weight = torch.cat(v_weight, dim=0)
                name = name.replace("key_value", "qkv_proj")
                if is_pp_missing_parameter(name, self):
                    continue
                param = params_dict[name]
                weight_loader = param.weight_loader
                weight_loader(param, k_weight, "k")
                weight_loader(param, v_weight, "v")
            elif "query" in name:
                name = name.replace("query", "qkv_proj")
                if is_pp_missing_parameter(name, self):
                    continue
                param = params_dict[name]
                weight_loader = param.weight_loader
                weight_loader(param, loaded_weight, "q")
            else:
                for param_name, weight_name, shard_id in stacked_params_mapping:
                    if weight_name not in name:
                        continue
                    name = name.replace(weight_name, param_name)
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
                    weight_loader = getattr(
                        param, "weight_loader", default_weight_loader
                    )
                    weight_loader(param, loaded_weight)
            loaded_params.add(name)
        return loaded_params