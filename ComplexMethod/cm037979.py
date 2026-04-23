def load_weight(self, weight: tuple[str, torch.Tensor]) -> str:
        stacked_params_mapping = [
            # (param_name, shard_name, shard_id)
            ("qkv_proj", "q_proj", "q"),
            ("qkv_proj", "k_proj", "k"),
            ("qkv_proj", "v_proj", "v"),
        ]
        params_mapping = []

        if self.is_causal:
            # For `WhisperCausalEncoder` we need
            # some more renaming
            stacked_params_mapping.extend(
                [
                    (".mlp.gate_up_proj", ".mlp.fc1", 0),
                    (".mlp.gate_up_proj", ".mlp.fc3", 1),
                ]
            )
            params_mapping.extend(
                [
                    (".mlp.down_proj", ".mlp.fc2"),
                ]
            )
        params_dict = dict(self.named_parameters())

        name, loaded_weight = weight
        for pattern, repl in self.mistral_remapping:
            if re.fullmatch(pattern, name):
                name = re.sub(pattern, repl, name)

        for param_name, weight_name, shard_id in stacked_params_mapping:
            if weight_name not in name:
                continue
            name = name.replace(weight_name, param_name)

            param = params_dict[name]
            weight_loader = param.weight_loader
            weight_loader(param, loaded_weight, shard_id)
            break
        else:
            for param_name, weight_name in params_mapping:
                if weight_name not in name:
                    continue
                name = name.replace(weight_name, param_name)

            param = params_dict[name]
            weight_loader = getattr(param, "weight_loader", default_weight_loader)
            weight_loader(param, loaded_weight)

        return name