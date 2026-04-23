def load_weights(self, weights: Iterable[tuple[str, torch.Tensor]]) -> set[str]:
        weights = self.hf_to_vllm_mapper.apply(weights)

        if self.config.hidden_act in ["silu", "geglu"]:
            stacked_params_mapping = [
                # (param_name, shard_name, shard_id)
                ("gate_up_proj", "gate_proj", 0),
                ("gate_up_proj", "up_proj", 1),
            ]
        else:
            stacked_params_mapping = []

        params_dict = dict(self.named_parameters())
        loaded_params: set[str] = set()
        for name, loaded_weight in weights:
            if not self.add_pooling_layer and "pooler" in name:
                continue
            for param_name, weight_name, shard_id in stacked_params_mapping:
                if weight_name not in name:
                    continue
                name = name.replace(weight_name, param_name)
                # Skip loading extra bias for GPTQ models.
                if name.endswith(".bias") and name not in params_dict:
                    continue
                param = params_dict[name]
                weight_loader = param.weight_loader
                weight_loader(param, loaded_weight, shard_id)
                break
            else:
                # Skip loading extra bias for GPTQ models.
                if name.endswith(".bias") and name not in params_dict:
                    continue
                param = params_dict[name]
                weight_loader = getattr(param, "weight_loader", default_weight_loader)
                if name.endswith((".w1", ".w2")):
                    # Nomic-MoE has fused experts weights
                    weight_loader(param, loaded_weight, name)
                else:
                    weight_loader(param, loaded_weight)
            loaded_params.add(name)
        return loaded_params