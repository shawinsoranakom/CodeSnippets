def _load_weights_quark(
        self,
        ep_rank_end: int,
        ep_rank_start: int,
        heads_per_rank: int,
        head_start: int,
        weights: Iterable[tuple[str, torch.Tensor]],
        stacked_params_mapping: list[tuple[str, ...]],
    ) -> set[str]:
        params_dict = dict(self.named_parameters())
        loaded_params: set[str] = set()

        use_ep = self.parallel_config.enable_expert_parallel
        num_experts = self.config.num_local_experts

        if use_ep:
            tp_rank = get_tensor_model_parallel_rank()
            tp_size = get_tensor_model_parallel_world_size()
        else:
            tp_size, tp_rank = FusedMoEParallelConfig.flatten_tp_across_dp_and_pcp(
                tp_size=get_tensor_model_parallel_world_size(),
                dp_size=get_dp_group().world_size,
                dp_rank=get_dp_group().rank_in_group,
                pcp_size=get_pcp_group().world_size,
                pcp_rank=get_pcp_group().rank_in_group,
            )

        def _is_mxfp4(weight_dtype: str | None) -> bool:
            """Return True for any MXFP4 weight-dtype variant.

            Covers "gpt_oss_mxfp4" (GptOssMxfp4MoEMethod) and "mxfp4"
            (QuarkMoEMethod with fp4 weights) and any future variants.
            """
            return weight_dtype is not None and "mxfp4" in weight_dtype

        def _get_moe_weight_dtype(layer_id: int = 0) -> str | None:
            """Helper function to get MoE quantization weight dtype.

            Args:
                layer_id: Layer index to check (default 0, as all layers should
                        have the same quantization method)

            Returns:
                Weight dtype string (e.g., "mxfp4", "fp8") or None if not available
            """
            if hasattr(self.layers[layer_id].mlp.experts.quant_method, "weight_dtype"):
                return self.layers[layer_id].mlp.experts.quant_method.weight_dtype
            return None

        intermediate_size = self.config.intermediate_size

        moe_weight_dtype = _get_moe_weight_dtype(layer_id=0)

        if _is_mxfp4(moe_weight_dtype):
            # MXFP4 requires OCP_MX_BLOCK_SIZE alignment
            intermediate_size_block = intermediate_size // OCP_MX_BLOCK_SIZE
            per_rank_intermediate_size_block = cdiv(intermediate_size_block, tp_size)
            per_rank_intermediate_size = (
                per_rank_intermediate_size_block * OCP_MX_BLOCK_SIZE
            )
        else:
            # FP8 and other formats don't need alignment
            per_rank_intermediate_size = cdiv(intermediate_size, tp_size)

        tp_rank_start = tp_rank * per_rank_intermediate_size
        tp_rank_end = min((tp_rank + 1) * per_rank_intermediate_size, intermediate_size)
        expert_params_mapping = self.get_expert_mapping()
        for name, loaded_weight in weights:
            if is_pp_missing_parameter(name, self):
                continue

            layer_id, expert_id, fused_name = None, None, None
            moe_quant_method = None
            if "experts" in name:
                parts = name.split(".")
                ids = [s for s in parts if s.isdigit()]

                # for amd-quark format that each expert is separated
                # need to extract the parameter name with experts fused.
                # example model: amd/gpt-oss-20b-MoE-Quant-W-MXFP4-A-FP8-KV-FP8
                if len(ids) == 2:
                    layer_id, expert_id = int(ids[0]), int(ids[-1])
                    parts.pop(len(parts) - 1 - parts[::-1].index(str(expert_id)))
                    fused_name = ".".join(parts)

                # for openai mxfp4 format that all experts are combined
                # no need to extract the parameter name with experts fused.
                # models: openai/gpt-oss-20b, openai/gpt-oss-120b
                elif len(ids) == 1:
                    layer_id, expert_id = int(ids[0]), None
                    fused_name = name

                else:
                    raise NameError(
                        f"Layer {name} contains more than 2 numeric indices. This is "
                        "an unexpected condition. Please open an issue if encountered."
                    )

                moe_quant_method = _get_moe_weight_dtype(layer_id=layer_id)

            def kv_cache_scale_loader(
                quant_config: QuantizationConfig,
                name: str,
                params_dict: dict[str, typing.Any],
                weight: torch.Tensor,
                default_weight_loader: Callable[..., None],
                loaded_params: set[str],
            ) -> tuple[bool, set[str]]:
                """
                Load KV cache output scales.
                Returns:
                    Tuple of (bool, set):
                    - bool: True if KV-cache scale was loaded into loaded_params
                    - set: Updated set of loaded_params if True else the original set
                """
                # load explicit cached KV output scale from quant_config
                if quant_config is not None and (
                    scale_name := quant_config.get_cache_scale(name)
                ):
                    param = params_dict[scale_name]
                    weight_loader = getattr(
                        param, "weight_loader", default_weight_loader
                    )
                    if weight.numel() != 1:
                        raise ValueError(
                            f"KV cache scale '{scale_name}' is expected to be a "
                            f"scalar, but got a tensor of shape {weight.shape}."
                        )
                    # Ensure weight is a scalar before passing to loader.
                    weight_loader(param, weight.flatten()[0])
                    loaded_params.add(scale_name)
                    return True, loaded_params

                return False, loaded_params

            load_kv_cache_scale_completed, loaded_params = kv_cache_scale_loader(
                self.quant_config,
                name,
                params_dict,
                loaded_weight,
                default_weight_loader,
                loaded_params,
            )
            if load_kv_cache_scale_completed:
                continue

            if (
                all(key in name for key in ["input_scale", "mlp.experts"])
                and expert_id is not None
            ):
                assert loaded_weight.numel() == 1
                expert_data = params_dict[fused_name].data[expert_id]
                expert_data.copy_(loaded_weight)
                loaded_params.add(fused_name)
                continue

            # Unified handler for mxfp4 weights and scales
            elif _is_mxfp4(moe_quant_method) and any(
                name.endswith(suffix)
                for suffix in [
                    ".w13_weight_scale",
                    ".w2_weight_scale",
                    ".w13_weight",
                    ".w2_weight",
                ]
            ):
                is_w13 = ".w13_" in name
                is_scale = "_scale" in name

                # Reshape weight for mxfp4 if needed (not for scales)
                if not is_scale and expert_id is None:
                    if is_w13:
                        if loaded_weight.dim() < 3:
                            raise ValueError(
                                f"Expected w13_weight to have at least 3 "
                                f"dimensions, got shape "
                                f"{loaded_weight.shape}"
                            )
                        if loaded_weight.shape[0] != num_experts:
                            raise ValueError(
                                f"Expected w13_weight first dimension to be "
                                f"{num_experts}, got "
                                f"{loaded_weight.shape[0]}"
                            )
                        loaded_weight = loaded_weight.view(
                            num_experts, 2 * intermediate_size, -1
                        ).contiguous()
                    else:
                        if loaded_weight.dim() < 3:
                            raise ValueError(
                                f"Expected w2_weight to have at least 3 "
                                f"dimensions, got shape "
                                f"{loaded_weight.shape}"
                            )
                        if loaded_weight.shape[0] != num_experts:
                            raise ValueError(
                                f"Expected w2_weight first dimension to be "
                                f"{num_experts}, got "
                                f"{loaded_weight.shape[0]}"
                            )
                        loaded_weight = loaded_weight.view(
                            num_experts, -1, intermediate_size // 2
                        ).contiguous()

                if use_ep:
                    sliced_weight = loaded_weight[ep_rank_start:ep_rank_end, ...]
                else:
                    if is_w13:
                        if expert_id is None:
                            sliced_weight = loaded_weight[
                                :, 2 * tp_rank_start : 2 * tp_rank_end, ...
                            ]
                        else:
                            sliced_weight = loaded_weight[
                                2 * tp_rank_start : 2 * tp_rank_end, ...
                            ]
                    else:
                        if is_scale:
                            sliced_weight = loaded_weight[
                                ...,
                                tp_rank_start // OCP_MX_BLOCK_SIZE : tp_rank_end
                                // OCP_MX_BLOCK_SIZE,
                            ]
                        else:
                            sliced_weight = loaded_weight[
                                ..., tp_rank_start // 2 : tp_rank_end // 2
                            ]

                # NOTE(rob): because gpt-oss ckpt has "unique" structure with
                # fused gate_up_proj fused on disk, we cannot use the existing
                # weight loaders without added complexity, so just do the
                # direct load here.
                param = params_dict[fused_name]
                expert_data = param.data[expert_id]
                dim1 = sliced_weight.shape[0]
                dim2 = sliced_weight.shape[1]
                expert_data.data[:dim1, :dim2].copy_(sliced_weight)
                loaded_params.add(fused_name)
                continue

            elif name.endswith(".w13_weight") and moe_quant_method == "fp8":
                if use_ep:
                    narrow_weight = loaded_weight[ep_rank_start:ep_rank_end, ...]
                else:
                    if expert_id is None:
                        narrow_weight = loaded_weight[
                            :, 2 * tp_rank_start : 2 * tp_rank_end, :
                        ]
                    else:
                        narrow_weight = loaded_weight[
                            2 * tp_rank_start : 2 * tp_rank_end, :
                        ]

                assert fused_name is not None
                param = params_dict[fused_name]

                if expert_id is None:
                    param.data.copy_(narrow_weight)
                else:
                    param.data[expert_id].copy_(narrow_weight)

                loaded_params.add(fused_name)
                continue

            elif name.endswith(".w13_weight_scale") and moe_quant_method == "fp8":
                assert fused_name is not None
                param = params_dict[fused_name]

                # Check if this is per-channel or per-tensor scale
                if loaded_weight.numel() > 1 and loaded_weight.dim() == 1:
                    if use_ep:
                        narrow_weight = loaded_weight[ep_rank_start:ep_rank_end, ...]
                    else:
                        narrow_weight = loaded_weight[
                            2 * tp_rank_start : 2 * tp_rank_end
                        ]
                else:
                    narrow_weight = loaded_weight

                if expert_id is None:
                    param.data.copy_(narrow_weight)
                else:
                    param.data[expert_id].copy_(narrow_weight)

                loaded_params.add(fused_name)
                continue

            elif name.endswith(".w13_input_scale") and moe_quant_method == "fp8":
                assert fused_name is not None
                param = params_dict[fused_name]

                if expert_id is None:
                    param.data.copy_(loaded_weight)
                else:
                    param.data[expert_id].copy_(loaded_weight)

                loaded_params.add(fused_name)
                continue

            elif name.endswith(".w2_weight") and moe_quant_method == "fp8":
                if use_ep:
                    narrow_weight = loaded_weight[ep_rank_start:ep_rank_end, ...]
                else:
                    if expert_id is None:
                        narrow_weight = loaded_weight[..., tp_rank_start:tp_rank_end]
                    else:
                        narrow_weight = loaded_weight[..., tp_rank_start:tp_rank_end]

                assert fused_name is not None
                param = params_dict[fused_name]

                if expert_id is None:
                    param.data.copy_(narrow_weight)
                else:
                    param.data[expert_id].copy_(narrow_weight)

                loaded_params.add(fused_name)
                continue

            elif name.endswith(".w2_weight_scale") and moe_quant_method == "fp8":
                assert fused_name is not None
                param = params_dict[fused_name]

                if use_ep:
                    narrow_weight = loaded_weight[ep_rank_start:ep_rank_end, ...]
                else:
                    narrow_weight = loaded_weight

                if expert_id is None:
                    param.data.copy_(narrow_weight)
                else:
                    param.data[expert_id].copy_(narrow_weight)

                loaded_params.add(fused_name)
                continue

            # Unified handler for bias loading (w13_bias and w2_bias)
            elif name.endswith(".w13_bias") or name.endswith(".w2_bias"):
                is_w13_bias = name.endswith(".w13_bias")

                if use_ep:
                    sliced_weight = loaded_weight[ep_rank_start:ep_rank_end, ...]
                else:
                    if is_w13_bias:
                        if expert_id is None:
                            sliced_weight = loaded_weight[
                                :, 2 * tp_rank_start : 2 * tp_rank_end
                            ]
                        else:
                            sliced_weight = loaded_weight[
                                2 * tp_rank_start : 2 * tp_rank_end
                            ]
                    else:
                        sliced_weight = loaded_weight
                        if tp_rank != 0:
                            sliced_weight = sliced_weight.zero_()

                # NOTE(rob): because gpt-oss ckpt has "unique" structure with
                # fused gate_up_proj fused on disk, we cannot use the existing
                # weight loaders without added complexity, so just do the
                # direct load here.
                assert fused_name is not None
                param = params_dict[fused_name]
                expert_data = param.data[expert_id]
                dim1 = sliced_weight.shape[0]
                expert_data.data[:dim1].copy_(sliced_weight)
                loaded_params.add(fused_name)
                continue

            elif "sinks" in name:
                # Handle attention sinks (distributed across ranks)
                param = params_dict[name]
                narrow_weight = loaded_weight.narrow(0, head_start, heads_per_rank)
                param.data.copy_(narrow_weight)
                loaded_params.add(name)
                continue

            for param_name, weight_name, shard_id in stacked_params_mapping:
                # Skip non-stacked layers and experts (experts handled below).
                if weight_name not in name:
                    continue
                # We have mlp.experts[0].gate_proj in the checkpoint.
                # Since we handle the experts below in expert_params_mapping,
                # we need to skip here BEFORE we update the name, otherwise
                # name will be updated to mlp.experts[0].gate_up_proj, which
                # will then be updated below in expert_params_mapping
                # for mlp.experts[0].gate_gate_up_proj, which breaks load.
                if ("mlp.experts." in name) and name not in params_dict:
                    continue
                name = name.replace(weight_name, param_name)

                if name.endswith("scale"):
                    # Remapping the name of FP8 kv-scale.
                    name = maybe_remap_kv_scale_name(name, params_dict)
                    if name is None:
                        continue

                param = params_dict[name]
                weight_loader = param.weight_loader

                weight_loader(param, loaded_weight, shard_id)
                loaded_params.add(name)
                break
            else:
                for mapping in expert_params_mapping:
                    # Anyway, this is an expert weight and should not be
                    # attempted to load as other weights later
                    param_name, weight_name, mapping_expert_id, shard_id = mapping
                    weight_name = (
                        weight_name[:-1] if weight_name.endswith(".") else weight_name
                    )

                    if weight_name not in name:
                        continue

                    param = params_dict[fused_name]
                    # We should ask the weight loader to return success or not
                    # here since otherwise we may skip experts with other
                    # available replicas.
                    weight_loader = typing.cast(
                        Callable[..., bool], param.weight_loader
                    )
                    # Use checkpoint's expert_id for quark format (when expert_id
                    # is extracted from weight name), otherwise use mapping's expert_id
                    actual_expert_id = (
                        expert_id if expert_id is not None else mapping_expert_id
                    )
                    success = weight_loader(
                        param,
                        loaded_weight,
                        fused_name,
                        shard_id=shard_id,
                        expert_id=actual_expert_id,
                        return_success=True,
                    )
                    if success:
                        name = fused_name
                        loaded_params.add(name)
                        break
                else:
                    if name not in params_dict:
                        continue
                    param = params_dict[name]
                    weight_loader = getattr(
                        param, "weight_loader", default_weight_loader
                    )
                    weight_loader(param, loaded_weight)

                loaded_params.add(name)
        return loaded_params