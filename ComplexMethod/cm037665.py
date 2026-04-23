def _find_matched_config(
        self, layer_name: str, module: torch.nn.Module
    ) -> dict[str, Any]:
        proj_name = layer_name.split(".")[-1]
        if proj_name in self.packed_modules_mapping:
            shard_proj_names = self.packed_modules_mapping[proj_name]

            # Convert fused_name --> [shard_names]
            shard_names = [
                layer_name.replace(proj_name, shard_proj_name)
                for shard_proj_name in shard_proj_names
            ]

            shard_configs = []
            for shard_name in shard_names:
                if shard_name == layer_name:
                    config = cast(
                        dict[str, Any], self.quant_config.get("global_quant_config")
                    )
                else:
                    config = self._find_matched_config(shard_name, module)
                shard_configs.append(config)

            if not all(
                deep_compare(q_config, shard_configs[0]) for q_config in shard_configs
            ):
                raise ValueError(
                    f"Found a different quantization configuration for "
                    f"{shard_proj_names} in {layer_name}. vLLM "
                    "requires all to use the same scheme."
                )
            return shard_configs[0]
        else:
            layer_quant_config = cast(
                dict[str, Any], self.quant_config.get("layer_quant_config")
            )

            def _matches_pattern(layer_name, pattern):
                if "*" not in pattern:
                    return layer_name in pattern
                return fnmatch.fnmatch(layer_name, pattern)

            for name_pattern, config in layer_quant_config.items():
                if _matches_pattern(layer_name, name_pattern):
                    return config

            layer_type = cast(str, type(module))
            layer_type_quant_config = cast(
                dict[str, Any], self.quant_config.get("layer_type_quant_config")
            )
            if layer_type in layer_type_quant_config:
                return layer_type_quant_config[layer_type]

            global_quant_config = cast(
                dict[str, Any], self.quant_config.get("global_quant_config")
            )
            return global_quant_config