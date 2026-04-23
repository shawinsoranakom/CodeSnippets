def load_weights(
        self,
        weights: Iterable[tuple[str, torch.Tensor]],
    ) -> set[str]:
        """Load weights with stacked gate+up and MoE expert remapping."""
        weights = _normalized_weights(weights)
        stacked_params_mapping = [
            ("gate_up_proj", "gate_proj", 0),
            ("gate_up_proj", "up_proj", 1),
        ]

        params_dict = dict(self.named_parameters(remove_duplicate=False))
        loaded_params: set[str] = set()
        expert_params_mapping = self.get_expert_mapping()

        for name, loaded_weight in weights:
            for param_name, weight_name, shard_id in stacked_params_mapping:
                if weight_name not in name:
                    continue
                if "mlp.experts" in name:
                    continue
                new_name = name.replace(weight_name, param_name)
                if new_name.endswith(".bias") and new_name not in params_dict:
                    continue
                if new_name not in params_dict:
                    continue
                if is_pp_missing_parameter(new_name, self):
                    continue

                param = params_dict[new_name]
                weight_loader = getattr(param, "weight_loader", default_weight_loader)
                weight_loader(param, loaded_weight, shard_id)
                loaded_params.add(new_name)
                break
            else:
                mapped = False
                for (
                    param_name,
                    weight_name,
                    expert_id,
                    shard_id,
                ) in expert_params_mapping:
                    if weight_name not in name:
                        continue

                    new_name = name.replace(weight_name, param_name)
                    if is_pp_missing_parameter(new_name, self):
                        continue
                    if new_name not in params_dict:
                        continue

                    param = params_dict[new_name]
                    weight_loader = getattr(
                        param, "weight_loader", default_weight_loader
                    )
                    weight_loader(
                        param,
                        loaded_weight,
                        name,
                        shard_id=shard_id,
                        expert_id=expert_id,
                    )
                    loaded_params.add(new_name)
                    mapped = True
                    break

                if mapped:
                    continue

                if name.endswith(".bias") and name not in params_dict:
                    continue
                if name not in params_dict:
                    continue
                if is_pp_missing_parameter(name, self):
                    continue

                param = params_dict[name]
                weight_loader = getattr(param, "weight_loader", default_weight_loader)
                weight_loader(param, loaded_weight)
                loaded_params.add(name)

        return loaded_params