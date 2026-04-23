def load_attn_mlp_weight(
        self,
        attn_mlp_replace_mapping: list[tuple[str, str, int]],
        params_dict: dict[str, Any],
        weight_name: str,
        loaded_weight: torch.Tensor,
        loaded_params: set[str],
    ) -> bool:
        for param_name, origin_name, shard_id in attn_mlp_replace_mapping:
            if origin_name not in weight_name or (
                ("mlp.experts." in weight_name) and weight_name not in params_dict
            ):
                continue
            weight_name_mapped = weight_name.replace(origin_name, param_name)
            if (
                param_name == "fused_qkv_a_proj"
                and weight_name_mapped not in params_dict
            ):
                continue
            else:
                weight_name = weight_name_mapped
            if weight_name.endswith(".bias") and weight_name not in params_dict:
                continue
            if is_pp_missing_parameter(weight_name, self):
                continue

            param = params_dict[weight_name]
            weight_loader = param.weight_loader
            weight_loader(param, loaded_weight, shard_id)
            loaded_params.add(weight_name)
            return True
        return False