def load_weights(self, weights: Iterable[tuple[str, torch.Tensor]]) -> set[str]:
        stacked_params_mapping = [
            # (param_name, shard_name, shard_id)
            ("qkv_proj", "q_proj", "q"),
            ("qkv_proj", "k_proj", "k"),
            ("qkv_proj", "v_proj", "v"),
        ]

        mlp_params_mapping: list[tuple[str, str, int]] = []
        expert_params_mapping: list[tuple[str, str, int]] = []

        for layer in range(self.config.num_hidden_layers):
            is_moe_layer = (layer + 1) % self.config.moe_layer_frequency == 0
            if is_moe_layer and self.config.use_residual:
                mlp_params_mapping.append(
                    (
                        f"layers.{layer}.residual_mlp.w13.weight",
                        f"layers.{layer}.residual_mlp.w1.weight",
                        0,
                    )
                )
                mlp_params_mapping.append(
                    (
                        f"layers.{layer}.residual_mlp.w13.weight",
                        f"layers.{layer}.residual_mlp.w3.weight",
                        1,
                    )
                )

            if is_moe_layer:
                for expert_id in range(self.config.num_local_experts):
                    expert_params_mapping.append(
                        ("ws", f"experts.{expert_id}.w1.weight", expert_id)
                    )
                    expert_params_mapping.append(
                        ("w2s", f"experts.{expert_id}.w2.weight", expert_id)
                    )
                    expert_params_mapping.append(
                        ("ws", f"experts.{expert_id}.w3.weight", expert_id)
                    )
            else:
                mlp_params_mapping.append(
                    (
                        f"layers.{layer}.block_sparse_moe.mlp.w13.weight",
                        f"layers.{layer}.block_sparse_moe.mlp.w1.weight",
                        0,
                    )
                )
                mlp_params_mapping.append(
                    (
                        f"layers.{layer}.block_sparse_moe.mlp.w13.weight",
                        f"layers.{layer}.block_sparse_moe.mlp.w3.weight",
                        1,
                    )
                )

        params_dict = dict(self.named_parameters())
        loaded_params: set[str] = set()

        for name, loaded_weight in weights:
            for param_name, weight_name, shard_id in stacked_params_mapping:
                if weight_name not in name:
                    continue
                name = name.replace(weight_name, param_name)
                # Skip loading extra bias for GPTQ models.
                if name.endswith(".bias") and name not in params_dict:
                    continue
                if is_pp_missing_parameter(name, self):
                    continue
                param = params_dict[name]
                weight_loader = param.weight_loader
                weight_loader(param, loaded_weight, shard_id)
                break
            else:
                for param_name, weight_name, shard_id in mlp_params_mapping:
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
                    for param_name, weight_name, shard_id in expert_params_mapping:
                        if weight_name not in name:
                            continue
                        name = name.replace(weight_name, param_name)
                        if is_pp_missing_parameter(name, self):
                            continue
                        param = params_dict[name]
                        weight_loader = param.weight_loader
                        weight_loader(
                            param, loaded_weight, weight_name, expert_id=shard_id
                        )
                        break
                    else:
                        if name.endswith(".bias") and name not in params_dict:
                            continue
                        if is_pp_missing_parameter(name, self):
                            continue
                        param = params_dict[name]
                        weight_loader = getattr(
                            param, "weight_loader", default_weight_loader
                        )
                        weight_loader(param, loaded_weight)
            loaded_params.add(name)
        return loaded_params