def load_weights(self, weights: Iterable[tuple[str, torch.Tensor]]) -> set[str]:
        params_dict = dict(self.named_parameters())
        loaded_params: set[str] = set()

        def which_layer(name: str) -> int:
            if "layers" in name:
                after_layer = name.split("layers")[-1]
                return int(after_layer.split(".")[1])
            return None

        def is_linear_attn_layer(layer_idx: int) -> bool:
            if layer_idx is None or layer_idx >= len(self.decoder_attention_types):
                return False
            return self.decoder_attention_types[layer_idx] == 0

        def is_moe_weight(name: str) -> bool:
            return "block_sparse_moe" in name and not name.endswith(".bias")

        def get_expert_id(param_name):
            pattern = r"layers\.\d+\.block_sparse_moe\.experts\.(\d+)\."
            match = re.search(pattern, param_name)
            if match:
                return match.group(1)
            return None

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

        def is_shared_mlp_weight(name: str) -> bool:
            return "shared_mlp" in name and not name.endswith(".bias")

        def load_shared_mlp_weight(
            name: str, loaded_weight: torch.Tensor, self
        ) -> None:
            if not self.CONCAT_FFN:
                if "gate_proj" in name:
                    name = name.replace("gate_proj", "w1", 1)
                elif "up_proj" in name:
                    name = name.replace("up_proj", "w3", 1)
                elif "down_proj" in name:
                    name = name.replace("down_proj", "w2", 1)
            else:
                if "gate_proj" in name:
                    name = name.replace("gate_proj", "gate_up_proj", 1)
                    loaded_shard_id = 0
                elif "up_proj" in name:
                    name = name.replace("up_proj", "gate_up_proj", 1)
                    loaded_shard_id = 1
            if is_pp_missing_parameter(name, self):
                return
            param = params_dict[name]
            weight_loader = getattr(param, "weight_loader", default_weight_loader)
            weight_loader = weight_loader_with_alias(name)(weight_loader)
            if not self.CONCAT_FFN:
                weight_loader(param, loaded_weight)
            else:
                if "gate_up_proj" in name:
                    weight_loader(param, loaded_weight, loaded_shard_id)
                elif "down_proj" in name:
                    weight_loader(param, loaded_weight)
                else:
                    raise AssertionError("MLP weight not in [gate_up_proj, down_proj]")
            loaded_params.add(name)
            return

        def is_mha_weight(name: str) -> bool:
            return "self_attn" in name and not name.endswith(".bias")

        def load_linear_attn_weight(
            name: str, loaded_weight: torch.Tensor, self
        ) -> None:
            if is_pp_missing_parameter(name, self):
                return
            param = params_dict[name]

            weight_loader = getattr(
                param, "weight_loader", MiniMaxText01LinearAttention.weight_direct_load
            )
            weight_loader = weight_loader_with_alias(name)(weight_loader)
            weight_loader(param, loaded_weight)
            loaded_params.add(name)
            return

        def load_flash_attn_weight(
            name: str, loaded_weight: torch.Tensor, self
        ) -> None:
            flash_mha_params_mapping = [
                ("qkv_proj", "q_proj", "q"),
                ("qkv_proj", "k_proj", "k"),
                ("qkv_proj", "v_proj", "v"),
                ("gate_up_proj", "gate_proj", 0),
                ("gate_up_proj", "up_proj", 1),
            ]
            for param_name, weight_name, shard_id in flash_mha_params_mapping:
                if weight_name not in name:
                    continue
                name = name.replace(weight_name, param_name)
                if is_pp_missing_parameter(name, self):
                    return
                param = params_dict[name]
                weight_loader = getattr(param, "weight_loader", default_weight_loader)
                weight_loader = weight_loader_with_alias(name)(weight_loader)
                weight_loader(param, loaded_weight, shard_id)
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

        def is_layer_norm_weight(name: str) -> bool:
            return "norm" in name and not name.endswith(".bias") and name in params_dict

        def load_layer_norm_weight(
            name: str, loaded_weight: torch.Tensor, self
        ) -> None:
            if is_pp_missing_parameter(name, self):
                return
            param = params_dict[name]
            weight_loader = getattr(param, "weight_loader", default_weight_loader)
            weight_loader = weight_loader_with_alias(name)(weight_loader)
            weight_loader(param, loaded_weight)
            loaded_params.add(name)
            return

        def load_basic_weight(name: str, loaded_weight: torch.Tensor, self) -> None:
            if is_pp_missing_parameter(name, self):
                return
            param = params_dict[name]
            weight_loader = getattr(param, "weight_loader", default_weight_loader)
            weight_loader = weight_loader_with_alias(name)(weight_loader)
            weight_loader(param, loaded_weight)
            loaded_params.add(name)
            return

        for name, loaded_weight in weights:
            weight_at_layer = which_layer(name)
            if weight_at_layer and weight_at_layer >= len(self.decoder_attention_types):
                continue

            if is_layer_norm_weight(name):
                load_layer_norm_weight(name, loaded_weight, self)
                continue
            if is_mha_weight(name):
                if is_linear_attn_layer(weight_at_layer):
                    load_linear_attn_weight(name, loaded_weight, self)
                else:
                    load_flash_attn_weight(name, loaded_weight, self)
                continue
            if is_moe_weight(name):
                load_sparse_moe_weight(name, loaded_weight, self)
                continue
            if is_shared_mlp_weight(name):
                load_shared_mlp_weight(name, loaded_weight, self)
                continue

            if "rotary_emb.inv_freq" in name:
                continue

            load_basic_weight(name, loaded_weight, self)
        return loaded_params