def load_weights(self, weights: Iterable[tuple[str, torch.Tensor]]) -> set[str]:
        stacked_params_mapping = [
            # (param_name, shard_name, shard_id)
            (".qkv_proj", ".q_proj", "q"),
            (".qkv_proj", ".k_proj", "k"),
            (".qkv_proj", ".v_proj", "v"),
        ]
        params_dict = dict(self.named_parameters())
        loaded_params: set[str] = set()
        expert_params_mapping = self.get_expert_mapping()

        def _load(n, p):
            param = params_dict[n]
            weight_loader = getattr(param, "weight_loader", default_weight_loader)
            weight_loader(param, p)
            loaded_params.add(n)

        def _load_shard(n, p, shard_id):
            # Skip layers on other devices.
            if not is_pp_missing_parameter(n, self):
                param = params_dict[n]
                weight_loader = getattr(param, "weight_loader", default_weight_loader)
                weight_loader(param, p, shard_id)
                loaded_params.add(n)

        def _load_expert(n, p, name, shard_id, expert_id):
            param = params_dict[n]
            weight_loader = getattr(param, "weight_loader", default_weight_loader)
            weight_loader(param, p, name, shard_id=shard_id, expert_id=expert_id)
            loaded_params.add(n)

        def _load_quant_expert(name, loaded_weight):
            for mapping in expert_params_mapping:
                param_name, weight_name, expert_id, shard_id = mapping

                if weight_name not in name:
                    continue

                name_mapped = name.replace(weight_name, param_name)

                # Skip layers on other devices.
                if is_pp_missing_parameter(name_mapped, self):
                    continue

                param = params_dict[name_mapped]
                weight_loader = param.weight_loader
                success = False

                if weight_loader is not None:
                    success = weight_loader(
                        param,
                        loaded_weight,
                        name_mapped,
                        shard_id=shard_id,
                        expert_id=expert_id,
                        return_success=True,
                    )

                if success:
                    return name_mapped
            return None

        for n, p in weights:
            if "A_log" in n:
                n = n.replace("A_log", "A")

            if self.quant_config is not None and (
                scale_name := self.quant_config.get_cache_scale(n)
            ):
                # Loading kv cache quantization scales
                loaded_weight = p
                loaded_weight = (
                    loaded_weight if loaded_weight.dim() == 0 else loaded_weight[0]
                )
                _load(scale_name, loaded_weight)
                loaded_params.add(scale_name)
                continue

            if _load_quant_expert(n, p):
                continue

            # Logic analogous to: https://github.com/vllm-project/vllm/blob/f49e5aff11c986ed4d45202b1716c5d74786efa9/vllm/model_executor/models/granitemoeshared.py#L215
            # Mapping different experts' layout:
            #  from HF (input_linear, output_linear, router)
            #  to vLLM (experts_w13({e}.w1, {e}.w2), experts_w3({e}.w3), gate)
            # The renaming and parameter loading logic is the same for weight
            # and weight_scale tensors so we can reuse them without issues.
            if n.endswith(".block_sparse_moe.input_linear.weight") or n.endswith(
                ".block_sparse_moe.input_linear.weight_scale"
            ):
                for e in range(p.size(0)):
                    w1_name = n.replace(
                        ".block_sparse_moe.input_linear.weight",
                        f".block_sparse_moe.experts.{e}.w1.weight",
                    )
                    w3_name = n.replace(
                        ".block_sparse_moe.input_linear.weight",
                        f".block_sparse_moe.experts.{e}.w3.weight",
                    )
                    w1_param, w3_param = p[e].chunk(2, dim=0)
                    _load_expert(
                        n.replace(".input_linear.", ".experts.w13_"),
                        w1_param,
                        w1_name,
                        shard_id="w1",
                        expert_id=e,
                    )
                    _load_expert(
                        n.replace(".input_linear.", ".experts.w13_"),
                        w3_param,
                        w3_name,
                        shard_id="w3",
                        expert_id=e,
                    )
            elif n.endswith(".block_sparse_moe.output_linear.weight") or n.endswith(
                ".block_sparse_moe.output_linear.weight_scale"
            ):
                for e in range(p.size(0)):
                    w2_name = n.replace(
                        ".block_sparse_moe.output_linear.weight",
                        f".block_sparse_moe.experts.{e}.w2.weight",
                    )
                    w2_param = p[e]
                    _load_expert(
                        n.replace(".output_linear.", ".experts.w2_"),
                        w2_param,
                        w2_name,
                        shard_id="w2",
                        expert_id=e,
                    )
            elif n.endswith(".block_sparse_moe.router.layer.weight"):
                gate_name = n.replace(
                    ".block_sparse_moe.router.layer.weight",
                    ".block_sparse_moe.gate.weight",
                )
                _load(gate_name, p)
            else:
                loaded = False
                for param_name, weight_name, shard_id in stacked_params_mapping:
                    if weight_name in n:
                        _load_shard(
                            n.replace(weight_name, param_name), p, shard_id=shard_id
                        )
                        loaded = True
                if not loaded:
                    _load(n, p)

        return loaded_params