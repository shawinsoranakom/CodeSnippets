def load_weights(self, weights: Iterable[tuple[str, torch.Tensor]]) -> set[str]:
        # Name mapping from the parameter name to the shard name and
        # corresponding shard id.
        stacked_params_mapping = [
            # (param_name, shard_name, shard_id)
            (".qkv_proj", ".q_proj", "q"),
            (".qkv_proj", ".k_proj", "k"),
            (".qkv_proj", ".v_proj", "v"),
            (".gate_up_proj", ".gate_proj", 0),
            (".gate_up_proj", ".up_proj", 1),
        ]
        # Indicate whether the expert weights are fused into a single weight
        # tensor.
        fused_experts_params = False
        # Expert parameter mapping for the case where the expert weights are
        # not fused into a single weight tensor.
        expert_params_mapping = FusedMoE.make_expert_params_mapping(
            self,
            ckpt_gate_proj_name="gate_proj",
            ckpt_down_proj_name="down_proj",
            ckpt_up_proj_name="up_proj",
            num_experts=self.num_experts,
            num_redundant_experts=self.n_redundant_experts,
        )
        # Expert parameter mapping for the case where the expert weights are
        # fused into a single weight tensor.
        expert_params_mapping_fused = FusedMoE.make_expert_params_mapping(
            self,
            ckpt_gate_proj_name="gate_up_proj",
            ckpt_down_proj_name="down_proj",
            ckpt_up_proj_name="gate_up_proj",
            num_experts=1,
        )
        # All the module parameters.
        params_dict = dict(self.named_parameters())
        # The module parameters that have been loaded.
        loaded_params: set[str] = set()

        # Iterate over all the weights and load them into module parameters.
        for name, loaded_weight in weights:
            # If the name contains "experts.gate_up_proj" or "experts.down_proj"
            # without the expert indices, it means the expert weights are fused
            # into a single weight tensor across all experts.
            if "experts.gate_up_proj" in name or "experts.down_proj" in name:
                fused_experts_params = True
                expert_params_mapping = expert_params_mapping_fused

            # If kv cache quantization scales exist and the weight name
            # corresponds to one of the kv cache quantization scales, load
            # them.
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

            # Iterate over stacked_params_mapping to check if the current weight
            # is one of the stacked parameters. If so, load the weight with the
            # corresponding shard id. Note that MoE weights are handled
            # separately in the else block.
            for param_name, weight_name, shard_id in stacked_params_mapping:
                # Skip if the current weight is not one of the stacked
                # parameters or if the current weight is a MoE weight.
                if weight_name not in name or "experts" in name:
                    continue

                # For ModelOpt checkpoints, we need to rename the self_attn
                # weight/weight_scale names except for kv cache scales.
                if not (
                    name.endswith((".k_scale", ".v_scale")) and "self_attn" in name
                ):
                    name = name.replace(weight_name, param_name)

                # Skip if the current weight corresponds to a parameter that
                # does not exist on the current PP (pipeline parallel) rank.
                if is_pp_missing_parameter(name, self):
                    continue

                # Remap kv cache scale names for ModelOpt checkpoints.
                # TODO: ModelOpt should implement get_cache_scale() such that
                #       kv cache scale name remapping can be done there.
                if name.endswith("scale"):
                    name = maybe_remap_kv_scale_name(name, params_dict)
                    if name is None:
                        continue

                # Load the weight into the module parameter with corresponding
                # shard id and exit the for loop and the else block.
                param = params_dict[name]
                weight_loader = getattr(param, "weight_loader", default_weight_loader)

                if weight_loader == default_weight_loader:
                    weight_loader(param, loaded_weight)
                else:
                    weight_loader(param, loaded_weight, shard_id)

                loaded_params.add(name)
                break

            # Handle normal (non-stacked) weights and MoE weights.
            else:
                # First, try to load MoE weights using load_moe_expert_weights.
                # If successful, move on to next loaded weight.
                if self.load_moe_expert_weights(
                    name,
                    loaded_weight,
                    params_dict,
                    loaded_params,
                    expert_params_mapping,
                    fused=fused_experts_params,
                ):
                    continue

                # Skip if the current weight corresponds to a parameter that
                # does not exist on the current PP (pipeline parallel) rank.
                if is_pp_missing_parameter(name, self):
                    continue

                # Handle flat expert scale parameters that don't match
                # per-expert patterns, i.e. one weight scale tensor for all
                # experts.
                scale_names = [
                    "w13_input_scale",
                    "w13_weight_scale",
                    "w2_input_scale",
                    "w2_weight_scale",
                ]
                if "experts." in name and any(
                    scale_name in name for scale_name in scale_names
                ):
                    param = params_dict[name]
                    weight_loader = getattr(
                        param, "weight_loader", default_weight_loader
                    )

                    # If weight loader supports special moe loading, use it to
                    # avoid expensive runtime reflection
                    if getattr(weight_loader, "supports_moe_loading", False):
                        # Map the weight name to the corresponding shard id.
                        shard_id = "w2" if "w2_" in name else "w1"

                        # Transpose if weight scales are FP8 block scales with
                        # three dimensions:
                        # [num_experts, hidden_in, hidden_out].
                        if (
                            name.endswith("weight_scale")
                            and loaded_weight.dtype == torch.float8_e4m3fn
                            and loaded_weight.ndim == 3
                        ):
                            loaded_weight = loaded_weight.transpose(-1, -2)

                        # Load the weight into the module parameter with
                        # corresponding shard id and expert id.
                        weight_loader(
                            param, loaded_weight, name, shard_id=shard_id, expert_id=0
                        )

                    else:
                        # Regular weight loader (handles both
                        # param.weight_loader and default_weight_loader)
                        weight_loader(param, loaded_weight)

                    loaded_params.add(name)
                    continue

                # Handle normal (non-stacked, non-MoE) weights.
                param = params_dict[name]
                weight_loader = getattr(param, "weight_loader", default_weight_loader)
                weight_loader(param, loaded_weight)
                loaded_params.add(name)

        # Finally, return the set of loaded parameters.
        return loaded_params