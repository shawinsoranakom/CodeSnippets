def load_weights(self, weights: Iterable[tuple[str, torch.Tensor]]) -> set[str]:
        qkv_params_mapping = [
            # (param_name, shard_name, relative_start_idx, relative_end_idx)
            (
                ".qkv_proj",
                ".q_proj",
                0,
                self.config.share_q_dim
                / (self.config.share_q_dim + self.config.head_dim * 2),
            ),
            (
                ".qkv_proj",
                ".k_proj",
                self.config.share_q_dim
                / (self.config.share_q_dim + self.config.head_dim * 2),
                (self.config.share_q_dim + self.config.head_dim)
                / (self.config.share_q_dim + self.config.head_dim * 2),
            ),
            (
                ".qkv_proj",
                ".v_proj",
                (self.config.share_q_dim + self.config.head_dim)
                / (self.config.share_q_dim + self.config.head_dim * 2),
                (self.config.share_q_dim + self.config.head_dim * 2)
                / (self.config.share_q_dim + self.config.head_dim * 2),
            ),
        ]
        stacked_params_mapping = [
            # (param_name, shard_name, shard_id)
            (".gate_up_proj", ".gate_proj", 0),
            (".gate_up_proj", ".up_proj", 1),
        ]
        params_dict = dict(self.named_parameters())
        loaded_params: set[str] = set()
        base_layer = (
            "base_layer." if any(".base_layer." in name for name in params_dict) else ""
        )

        expert_params_mapping = [
            (f".moe.experts.{base_layer}w13_weight", ".moe.gate_proj.weight", "w1"),
            (f".moe.experts.{base_layer}w13_weight", ".moe.up_proj.weight", "w3"),
            (f".moe.experts.{base_layer}w2_weight", ".moe.down_proj.weight", "w2"),
        ]

        disable_moe_stacked_params = [data[1] for data in expert_params_mapping]

        for name, loaded_weight in weights:
            for param_name, weight_name, shard_id in stacked_params_mapping:
                if weight_name not in name:
                    continue
                if any(
                    disable_moe_stacked_param in name
                    for disable_moe_stacked_param in disable_moe_stacked_params
                ):
                    continue
                name = name.replace(weight_name, param_name)
                if is_pp_missing_parameter(name, self):
                    continue
                param = params_dict[name]
                weight_loader = param.weight_loader
                weight_loader(param, loaded_weight, shard_id)
                loaded_params.add(name)
                break
            else:
                for mapping in expert_params_mapping:
                    param_name, weight_name, shard_id = mapping
                    if weight_name not in name:
                        continue
                    name = name.replace(weight_name, param_name)
                    # Skip layers on other devices.
                    if is_pp_missing_parameter(name, self):
                        continue
                    # Skip loading extra bias for GPTQ models.
                    if (
                        name.endswith(".bias") or name.endswith("_bias")
                    ) and name not in params_dict:
                        continue
                    param = params_dict[name]
                    weight_loader = param.weight_loader
                    for expert_id in range(loaded_weight.shape[0]):
                        loaded_weight_expert = loaded_weight[expert_id]
                        weight_loader(
                            param,
                            loaded_weight_expert,
                            name,
                            shard_id=shard_id,
                            expert_id=expert_id,
                        )
                    loaded_params.add(name)
                    break
                else:
                    for (
                        param_name,
                        weight_name,
                        start_idx,
                        end_idx,
                    ) in qkv_params_mapping:
                        if weight_name not in name:
                            continue
                        name = name.replace(weight_name, param_name)
                        if is_pp_missing_parameter(name, self):
                            continue
                        param = params_dict[name]
                        dim = param.shape[param.output_dim]
                        begin_idx = int(start_idx * dim)
                        end_idx = int(end_idx * dim)
                        param_slice = param.narrow(
                            param.output_dim, begin_idx, end_idx - begin_idx
                        )
                        param_slice.copy_(loaded_weight)
                        loaded_params.add(name)
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