def load_weights(self, weights: Iterable[tuple[str, torch.Tensor]]) -> set[str]:
        stacked_params_mapping = [
            # (param_name, shard_name, shard_id)
            ("qkv_proj", "q_proj", "q"),
            ("qkv_proj", "k_proj", "k"),
            ("qkv_proj", "v_proj", "v"),
            ("gate_up_proj", "gate_proj", 0),
            ("gate_up_proj", "up_proj", 1),
        ]

        # MoE expert weight mapping: checkpoint can have either:
        #   1. 3D packed tensors (exploded in _weight_iterator to per-expert 2D)
        #   2. Already per-expert 2D weights (if quantized)
        # Map to FusedMoE parameters:
        #   moe.experts.{id}.gate_proj → FusedMoE w1 (shard of w13)
        #   moe.experts.{id}.up_proj   → FusedMoE w3 (shard of w13)
        #   moe.experts.{id}.down_proj → FusedMoE w2
        #
        # Use prefix matching to handle both weights and
        # quantization scale parameters. The param_name is a prefix ending
        # in underscore, and weight_name ends with a dot, so that:
        #   "experts.0.gate_proj.weight_scale" -> "experts.w13_weight_scale"
        #   "experts.0.gate_proj.weight" -> "experts.w13_weight"
        num_experts = getattr(self.config, "num_experts", None) or 0
        expert_params_mapping = [
            # (param_name, weight_name, expert_id, shard_id)
            (
                "experts.w13_"
                if proj_name in ["gate_proj", "up_proj"]
                else "experts.w2_",
                f"experts.{expert_id}.{proj_name}.",
                expert_id,
                shard_id,
            )
            for expert_id in range(num_experts)
            for shard_id, proj_name in [
                ("w1", "gate_proj"),
                ("w2", "down_proj"),
                ("w3", "up_proj"),
            ]
        ]
        params_dict = dict(self.named_parameters())
        # Include buffers (e.g. layer_scalar) so they can be loaded too
        params_dict.update(dict(self.named_buffers()))
        loaded_params: set[str] = set()
        for name, loaded_weight in weights:
            if self.quant_config is not None and (
                scale_name := self.quant_config.get_cache_scale(name)
            ):
                param = params_dict[scale_name]
                weight_loader = getattr(param, "weight_loader", default_weight_loader)
                loaded_weight = loaded_weight[0]
                weight_loader(param, loaded_weight)
                loaded_params.add(scale_name)
                continue

            if name.endswith((".k_scale", ".v_scale", ".q_scale", ".prob_scale")):
                remapped_name = maybe_remap_kv_scale_name(name, params_dict)
                if remapped_name is not None and remapped_name in params_dict:
                    param = params_dict[remapped_name]
                    weight_loader = getattr(
                        param, "weight_loader", default_weight_loader
                    )
                    weight_loader(param, loaded_weight)
                    loaded_params.add(remapped_name)
                    continue

            for param_name, shard_name, shard_id in stacked_params_mapping:
                if shard_name not in name:
                    continue
                stacked_name = name.replace(shard_name, param_name)
                # k_eq_v layers use separate q_proj/k_proj instead of
                # packed qkv_proj. If the stacked param doesn't exist,
                # skip this mapping and fall through to direct load.
                if stacked_name not in params_dict:
                    continue
                if is_pp_missing_parameter(stacked_name, self):
                    continue
                param = params_dict[stacked_name]
                weight_loader = param.weight_loader
                weight_loader(param, loaded_weight, shard_id)
                loaded_params.add(stacked_name)
                break
            else:
                for (
                    param_name,
                    weight_name,
                    expert_id,
                    shard_id,
                ) in expert_params_mapping:
                    # Match both:
                    #  - Bare weights: "experts.0.down_proj" (from 3D explosion)
                    #  - With suffix: "experts.0.down_proj.weight_scale" (2D quantized)
                    # weight_name has trailing dot, so check with and without it
                    weight_name_base = weight_name.rstrip(".")
                    if weight_name in name:
                        # Has suffix (e.g., .weight_scale)
                        moe_name = name.replace(weight_name, param_name)
                    elif name.endswith(weight_name_base):
                        # Bare weight (no suffix)
                        moe_name = name.replace(
                            weight_name_base, param_name.rstrip("_") + "_weight"
                        )
                    else:
                        continue
                    if moe_name not in params_dict:
                        continue
                    if is_pp_missing_parameter(moe_name, self):
                        continue
                    param = params_dict[moe_name]
                    # Expert weights are already in the correct
                    # orientation for FusedMoE after _weight_iterator:
                    #   gate/up: [I, H] → w1/w3 expects [I, H]
                    #   down:    [H, I] → w2 expects [H, I]
                    # Scales and other quantization params may be 1D or scalar.
                    weight_loader = param.weight_loader
                    weight_loader(
                        param,
                        loaded_weight,
                        moe_name,  # Pass mapped name (handles both weights and scales)
                        shard_id=shard_id,
                        expert_id=expert_id,
                    )
                    loaded_params.add(moe_name)
                    break
                else:
                    if name.endswith(".bias") and name not in params_dict:
                        continue
                    name = maybe_remap_kv_scale_name(name, params_dict)
                    if name is None:
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