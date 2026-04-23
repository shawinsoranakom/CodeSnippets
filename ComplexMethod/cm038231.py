def load_weights(self, weights: Iterable[tuple[str, torch.Tensor]]) -> set[str]:
        config = self.config
        assert config.num_attention_groups > 1, "Only support GQA"
        qkv_params_mapping = []
        stacked_params_mapping = [
            # (param_name, shard_name, shard_id)
            ("qkv_proj", "q_proj", "q"),
            ("qkv_proj", "k_proj", "k"),
            ("qkv_proj", "v_proj", "v"),
            ("gate_up_proj", "gate_proj", 0),
            ("gate_up_proj", "up_proj", 1),
        ]

        params_dict = dict(self.named_parameters())
        loaded_params: set[str] = set()
        base_layer = (
            "base_layer." if any(".base_layer." in name for name in params_dict) else ""
        )

        # Old packed 3D format: .moe.gate_proj.weight [num_experts, out, in]
        expert_params_mapping = [
            (f".moe.experts.{base_layer}w13_weight", ".moe.gate_proj.weight", "w1"),
            (f".moe.experts.{base_layer}w13_weight", ".moe.up_proj.weight", "w3"),
            (f".moe.experts.{base_layer}w2_weight", ".moe.down_proj.weight", "w2"),
        ]

        # New per-expert format: .moe.experts.E.gate_proj.weight_packed [out, in]
        per_expert_mapping = FusedMoE.make_expert_params_mapping(
            self,
            ckpt_gate_proj_name="gate_proj",
            ckpt_down_proj_name="down_proj",
            ckpt_up_proj_name="up_proj",
            num_experts=self.moe_num_experts,
        )

        disable_moe_stacked_params = [data[1] for data in expert_params_mapping]

        for name, loaded_weight in weights:
            if name.startswith("model."):
                local_name = name[len("model.") :]
                full_name = name
            else:
                local_name = name
                full_name = f"model.{name}" if name else "model"

            spec_layer = get_spec_layer_idx_from_weight_name(config, full_name)
            if spec_layer is not None:
                continue  # skip spec decode layers for main model

            # Skip any layers beyond the main model's depth (e.g., MTP layers)
            if full_name.startswith("model.layers."):
                parts = full_name.split(".")
                if len(parts) > 2 and parts[2].isdigit():
                    layer_idx = int(parts[2])
                    if layer_idx >= config.num_hidden_layers:
                        continue

            # Per-expert MoE weights (new format from LLM Compressor):
            # .moe.experts.{E}.{gate,up,down}_proj.{weight_packed,scale,...}
            # Each weight is individual per-expert, not stacked 3D.
            if ".moe.experts." in local_name:
                is_expert_weight = False
                for mapping in per_expert_mapping:
                    param_name, weight_name, expert_id, shard_id = mapping
                    if weight_name not in local_name:
                        continue
                    is_expert_weight = True
                    name_mapped = local_name.replace(weight_name, param_name)
                    if is_pp_missing_parameter(name_mapped, self):
                        continue
                    if name_mapped not in params_dict:
                        continue
                    param = params_dict[name_mapped]
                    weight_loader = typing.cast(
                        Callable[..., bool], param.weight_loader
                    )
                    success = weight_loader(
                        param,
                        loaded_weight,
                        name_mapped,
                        shard_id=shard_id,
                        expert_id=expert_id,
                        return_success=True,
                    )
                    if success:
                        loaded_params.add(name_mapped)
                        break
                else:
                    if (
                        not is_expert_weight
                        and not is_pp_missing_parameter(local_name, self)
                        and local_name in params_dict
                    ):
                        # Not an expert proj — use default loader
                        # (e.g. share_expert weights if they matched)
                        param = params_dict[local_name]
                        weight_loader = getattr(
                            param,
                            "weight_loader",
                            default_weight_loader,
                        )
                        weight_loader(param, loaded_weight)
                        loaded_params.add(local_name)
                continue

            for param_name, weight_name, shard_id in stacked_params_mapping:
                if weight_name not in local_name:
                    continue
                if any(
                    disable_moe_stacked_param in local_name
                    for disable_moe_stacked_param in disable_moe_stacked_params
                ):
                    continue
                replaced_name = local_name.replace(weight_name, param_name)
                if is_pp_missing_parameter(replaced_name, self):
                    continue
                if replaced_name not in params_dict:
                    continue
                param = params_dict[replaced_name]
                weight_loader = param.weight_loader
                weight_loader(param, loaded_weight, shard_id)
                loaded_params.add(replaced_name)
                break
            else:
                for param_name, weight_name, shard_id in expert_params_mapping:
                    if weight_name not in local_name:
                        continue
                    replaced_name = local_name.replace(weight_name, param_name)
                    if is_pp_missing_parameter(replaced_name, self):
                        continue
                    if (
                        replaced_name.endswith(".bias")
                        or replaced_name.endswith("_bias")
                    ) and replaced_name not in params_dict:
                        continue
                    if replaced_name not in params_dict:
                        continue
                    param = params_dict[replaced_name]
                    weight_loader = param.weight_loader
                    moe_expert_num = self.moe_num_experts
                    # Per-tensor global scales (e.g. weight_global_scale)
                    # have shape [1] in compressed-tensors NVFP4 checkpoints.
                    # Expand to per-expert before the iteration loop.
                    if (
                        loaded_weight.shape[0] == 1
                        and loaded_weight.shape[0] != moe_expert_num
                    ):
                        loaded_weight = loaded_weight.expand(
                            moe_expert_num, *loaded_weight.shape[1:]
                        )
                    assert loaded_weight.shape[0] == moe_expert_num
                    for expert_id in range(moe_expert_num):
                        loaded_weight_expert = loaded_weight[expert_id]
                        weight_loader(
                            param,
                            loaded_weight_expert,
                            replaced_name,
                            shard_id=shard_id,
                            expert_id=expert_id,
                        )
                    loaded_params.add(replaced_name)
                    break
                else:
                    for (
                        param_name,
                        weight_name,
                        start_idx,
                        end_idx,
                    ) in qkv_params_mapping:
                        if weight_name not in local_name:
                            continue
                        replaced_name = local_name.replace(weight_name, param_name)
                        if is_pp_missing_parameter(replaced_name, self):
                            continue
                        if replaced_name not in params_dict:
                            continue
                        param = params_dict[replaced_name]
                        dim = param.shape[param.output_dim]
                        begin_idx = int(start_idx * dim)
                        end_idx = int(end_idx * dim)
                        param_slice = param.narrow(
                            param.output_dim, begin_idx, end_idx - begin_idx
                        )
                        param_slice.copy_(loaded_weight)
                        loaded_params.add(replaced_name)
                        break
                    else:
                        if is_pp_missing_parameter(local_name, self):
                            continue
                        if "expert_bias" in local_name:
                            logger.warning_once("ignore expert_bias")
                            continue
                        if local_name not in params_dict:
                            continue
                        param = params_dict[local_name]
                        weight_loader = getattr(
                            param, "weight_loader", default_weight_loader
                        )
                        weight_loader(param, loaded_weight)
                        loaded_params.add(local_name)
        return loaded_params