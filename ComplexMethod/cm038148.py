def load_weights(self, weights: Iterable[tuple[str, torch.Tensor]]) -> set[str]:
        """Load checkpoint weights with simplified mapping."""

        params_dict = dict(self.named_parameters(remove_duplicate=False))
        loaded_params: set[str] = set()

        # Stacked parameter mappings (fused projections)
        stacked_mappings = [
            (".fused_qkv_a_proj", ".q_a_proj", 0),
            (".fused_qkv_a_proj", ".kv_a_proj_with_mqa", 1),
            (".gate_up_proj", ".gate_proj", 0),
            (".gate_up_proj", ".up_proj", 1),
        ]

        # Expert parameter mappings from FusedMoE
        expert_mappings = list(self.get_expert_mapping())

        def load_param(name: str, tensor: torch.Tensor, shard_id=None) -> bool:
            """Load a single parameter."""
            if name not in params_dict or is_pp_missing_parameter(name, self):
                return False
            if name.endswith(".bias") and name not in params_dict:
                return False

            param = params_dict[name]
            weight_loader = getattr(param, "weight_loader", default_weight_loader)

            if shard_id is None:
                weight_loader(param, tensor)
            elif isinstance(shard_id, int):
                weight_loader(param, tensor, shard_id)
            else:
                # Expert param: (expert_id, shard_id)
                weight_loader(
                    param, tensor, name, expert_id=shard_id[0], shard_id=shard_id[1]
                )

            loaded_params.add(name)
            return True

        def normalize_name(name: str) -> str | None:
            """Normalize checkpoint name to model parameter name."""
            # Skip special weights
            if name.startswith("model.mtp"):
                return None
            # Remove 'model.' prefix if present
            # (e.g., 'model.layers.0...' -> 'layers.0...')
            name = name.removeprefix("model.")
            # Map attention.dense based on layer type
            if "attention.dense" in name:
                layer_idx = (
                    int(name.split("layers.")[1].split(".")[0])
                    if "layers." in name
                    else 0
                )
                attn_name = (
                    "self_attn.dense"
                    if is_linear_layer(layer_idx, self.config.layer_group_size)
                    else "self_attn.o_proj"
                )
                name = name.replace("attention.dense", attn_name)

            # Standard mappings
            name = name.replace("attention.", "self_attn.")
            name = name.replace(
                "mlp.gate.e_score_correction_bias", "mlp.gate.expert_bias"
            )

            return maybe_remap_kv_scale_name(name, params_dict)

        for orig_name, weight in weights:
            norm_name = normalize_name(orig_name)
            if norm_name is None:
                continue

            # Try stacked mappings
            loaded = False
            for param_suf, weight_suf, shard_id in stacked_mappings:
                if weight_suf not in norm_name:
                    continue
                mapped = norm_name.replace(weight_suf, param_suf).replace(
                    "attention.", "self_attn."
                )
                if load_param(mapped, weight, shard_id):
                    loaded = True
                    break
            if loaded:
                continue

            # Handle expert weights
            if "mlp.experts" in norm_name:
                # Expert bias
                if (
                    "mlp.experts.e_score_correction_bias" in norm_name
                    or "mlp.experts.expert_bias" in norm_name
                ):
                    alt = norm_name.replace(
                        "mlp.experts.e_score_correction_bias", "mlp.gate.expert_bias"
                    ).replace("mlp.experts.expert_bias", "mlp.gate.expert_bias")
                    if load_param(alt, weight) or load_param(norm_name, weight):
                        continue

                # Routed experts
                for param_name, weight_name, expert_id, shard_id in expert_mappings:
                    if weight_name not in norm_name:
                        continue
                    mapped = norm_name.replace(weight_name, param_name)
                    if load_param(mapped, weight, (expert_id, shard_id)):
                        break
                continue

            # General parameters
            load_param(norm_name, weight)

        return loaded_params