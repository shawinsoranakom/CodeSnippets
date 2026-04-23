def load_weights(self, weights: Iterable[tuple[str, torch.Tensor]]) -> set[str]:
        """Load weights, mapping q/k/v projections to fused qkv_proj."""
        stacked_params_mapping = [
            (".qkv_proj", ".q_proj", "q"),
            (".qkv_proj", ".k_proj", "k"),
            (".qkv_proj", ".v_proj", "v"),
        ]

        params_dict = dict(self.named_parameters())
        loaded_params: set[str] = set()

        for name, loaded_weight in weights:
            if "rotary_emb.inv_freq" in name:
                continue
            if "rotary_emb.cos_cached" in name or "rotary_emb.sin_cached" in name:
                continue

            if self.quant_config is not None and (
                scale_name := self.quant_config.get_cache_scale(name)
            ):
                param = params_dict[scale_name]
                weight_loader = getattr(param, "weight_loader", default_weight_loader)
                loaded_weight = (
                    loaded_weight if loaded_weight.dim() == 0 else loaded_weight[0]
                )
                weight_loader(param, loaded_weight)
                loaded_params.add(scale_name)
                continue

            if "scale" in name or "zero_point" in name:
                remapped_name = maybe_remap_kv_scale_name(name, params_dict)
                if remapped_name is None:
                    continue
                name = remapped_name

            mapped = False
            for param_name, weight_name, shard_id in stacked_params_mapping:
                if weight_name not in name:
                    continue

                name = name.replace(weight_name, param_name)

                if name.endswith(".bias") and name not in params_dict:
                    mapped = True
                    break

                if is_pp_missing_parameter(name, self):
                    mapped = True
                    break

                param = params_dict[name]
                weight_loader = param.weight_loader  # type: ignore[attr-defined]
                weight_loader(param, loaded_weight, shard_id)
                loaded_params.add(name)
                mapped = True
                break

            if mapped:
                continue

            if name.endswith(".bias") and name not in params_dict:
                continue

            if is_pp_missing_parameter(name, self):
                continue

            param = params_dict[name]
            weight_loader = getattr(param, "weight_loader", default_weight_loader)
            weight_loader(param, loaded_weight)
            loaded_params.add(name)

        return loaded_params