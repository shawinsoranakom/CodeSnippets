def load_sparse_moe_weight(
            name: str, loaded_weight: torch.Tensor, self
        ) -> None:
            if isinstance(self.config.num_local_experts, list):
                expert_params_mapping = [
                    (
                        "w13_weight" if weight_name in ["w1", "w3"] else "w2_weight",
                        f"experts.{expert_id}.{weight_name}.weight",
                        expert_id,
                    )
                    for expert_id in range(max(self.config.num_local_experts))
                    for weight_name in ["w1", "w2", "w3"]
                ]
            else:
                expert_params_mapping = [
                    (
                        "w13_scale" if weight_name in ["w1", "w3"] else "w2_scale",
                        f"{expert_id}.{weight_name}.weight_scale",
                        expert_id,
                        weight_name,
                    )
                    for expert_id in range(self.config.num_local_experts)
                    for weight_name in ["w1", "w2", "w3"]
                ] + [
                    (
                        "w13_weight" if weight_name in ["w1", "w3"] else "w2_weight",
                        f"{expert_id}.{weight_name}.weight",
                        expert_id,
                        weight_name,
                    )
                    for expert_id in range(self.config.num_local_experts)
                    for weight_name in ["w1", "w2", "w3"]
                ]
            for param_name, weight_name, expert_id, shard_id in expert_params_mapping:
                name_expert_id = get_expert_id(name)
                if name_expert_id is not None and int(name_expert_id) != int(expert_id):
                    continue
                if weight_name not in name:
                    continue
                name = name.replace(weight_name, param_name)
                if is_pp_missing_parameter(name, self):
                    return
                param = params_dict[name]
                weight_loader = param.weight_loader
                weight_loader = weight_loader_with_alias(name)(weight_loader)
                weight_loader(
                    param,
                    loaded_weight,
                    weight_name,
                    expert_id=expert_id,
                    shard_id=shard_id,
                )
                loaded_params.add(name)
                break
            else:
                if is_pp_missing_parameter(name, self):
                    return
                param = params_dict[name]
                weight_loader = getattr(param, "weight_loader", default_weight_loader)
                weight_loader = weight_loader_with_alias(name)(weight_loader)
                weight_loader(param, loaded_weight)
                loaded_params.add(name)
            return