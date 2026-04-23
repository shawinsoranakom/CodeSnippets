def _weight_iterator():
            use_k_eq_v = getattr(self.config, "attention_k_eq_v", False)
            # Build set of k_eq_v layer indices (full_attention layers
            # when attention_k_eq_v is enabled). These layers have k_proj
            # but no v_proj in checkpoint — we duplicate k_proj as v_proj.
            k_eq_v_layer_indices: set[int] = set()
            if use_k_eq_v:
                for idx, lt in enumerate(self.config.layer_types):
                    if lt == "full_attention":
                        k_eq_v_layer_indices.add(idx)

            for name, weight in weights:
                # Remap "language_model." → "" to match our model tree.
                # Checkpoint: model.language_model.layers.X.*
                # Our model:  model.layers.X.*
                name = name.replace("language_model.", "")

                # Remap new HF checkpoint naming to internal vLLM
                # naming: HF moved per_expert_scale to router and
                # renamed moe → experts in the MoE block.
                name = name.replace(
                    ".router.per_expert_scale",
                    ".moe.per_expert_scale",
                )
                if ".experts.gate_up_proj" in name:
                    name = name.replace(
                        ".experts.gate_up_proj",
                        ".moe.gate_up_proj",
                    )
                elif ".experts.down_proj" in name:
                    name = name.replace(
                        ".experts.down_proj",
                        ".moe.down_proj",
                    )

                # Remap individual 2D expert weights:
                # .experts.{id}.{proj} → .moe.experts.{id}.{proj}
                # (This handles per-expert 2D quantized weights)
                name = re.sub(r"\.experts\.(\d+)\.", r".moe.experts.\1.", name)

                # MoE expert weights: checkpoint stores as 3D packed
                # tensors.  Explode into per-expert 2D weights for
                # FusedMoE weight_loader.
                #
                # Checkpoint format:
                #   moe.gate_up_proj: [E, 2*I, H]  (fused gate + up)
                #   moe.down_proj:    [E, H, I]
                #
                # FusedMoE expects per-expert:
                #   w1 (gate): [I, H]   — first half of gate_up
                #   w3 (up):   [I, H]   — second half of gate_up
                #   w2 (down): [H, I]   — as-is from checkpoint
                #
                # No transpose needed: checkpoint orientation already
                # matches FusedMoE's expected layout.
                if "moe.gate_up_proj" in name and weight.dim() == 3:
                    num_experts = weight.size(0)
                    intermediate_size = weight.size(1) // 2
                    for expert_id in range(num_experts):
                        gate_weight = weight[expert_id, :intermediate_size, :]
                        up_weight = weight[expert_id, intermediate_size:, :]
                        base = name.replace("moe.", f"moe.experts.{expert_id}.")
                        yield base.replace("gate_up_proj", "gate_proj"), gate_weight
                        yield base.replace("gate_up_proj", "up_proj"), up_weight
                    continue

                if "moe.down_proj" in name and weight.dim() == 3:
                    num_experts = weight.size(0)
                    for expert_id in range(num_experts):
                        expert_name = name.replace("moe.", f"moe.experts.{expert_id}.")
                        yield expert_name, weight[expert_id]
                    continue

                # k_eq_v layers: checkpoint has k_proj but no v_proj.
                # QKVParallelLinear expects both, so duplicate k_proj
                # as v_proj so V gets identical weights to K.
                # ONLY for full_attention layers — sliding layers have
                # their own real v_proj weights.
                if "self_attn.k_proj" in name and k_eq_v_layer_indices:
                    m = re.search(r"layers\.(\d+)\.", name)
                    if m and int(m.group(1)) in k_eq_v_layer_indices:
                        yield name, weight
                        yield name.replace("k_proj", "v_proj"), weight.clone()
                        continue

                yield name, weight