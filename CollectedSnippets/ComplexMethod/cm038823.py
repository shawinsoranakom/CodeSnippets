def create_dummy_lora(
        self,
        lora_id: int,
        rank: int,
        embedding_modules: dict[str, str] | None = None,
    ) -> LoRAModel:
        """Create zero-initialized LoRAModel for warmup."""
        model = LoRAModel(lora_id, rank, {})
        for module_name, module in self.model.named_modules():
            if (
                not self._match_target_modules(module_name)
                or not isinstance(module, BaseLayerWithLoRA)
                or self._get_punica_wrapper(module_name) is None
            ):
                continue
            parts = module_name.split(".")
            if module_name not in self.packed_modules:
                assert embedding_modules is not None
                if parts[-1] in embedding_modules:
                    # Special-case lm_head: wrapped by LogitsProcessorWithLoRA.
                    # LoRA input dim is hidden_size, output dim is vocab size.
                    # LogitsProcessorWithLoRA handles extra vocab size directly.
                    if parts[-1] == "lm_head":
                        input_dim = module.lora_a_stacked[0].shape[-1]
                        output_dim = module.lora_b_stacked[0].shape[-2]
                    else:
                        input_dim = (
                            module.base_layer.org_vocab_size
                            if hasattr(module.base_layer, "org_vocab_size")
                            else module.base_layer.weight.shape[1]
                        )
                        output_dim = (
                            module.base_layer.embedding_dim
                            if hasattr(module.base_layer, "embedding_dim")
                            else module.base_layer.weight.shape[0]
                        )
                    lora = LoRALayerWeights.create_dummy_lora_weights(
                        module_name,
                        input_dim,
                        output_dim,
                        rank,
                        module.lora_a_stacked[0].dtype,
                        "cpu",
                    )
                    model.loras[module_name] = lora
                elif module.__class__.__name__ == "FusedMoE3DWithLoRA":
                    # Case for 3D moe model
                    # w2
                    lora = LoRALayerWeights.create_dummy_lora_weights(
                        module_name,
                        module.w2_input_size,
                        module.w2_output_size,
                        rank * module.w2_lora_a_stacked[0].shape[1],  # rank*num_experts
                        module.w2_lora_a_stacked[0].dtype,
                        "cpu",
                    )
                    model.loras[module_name] = lora
                    # w13
                    lora = LoRALayerWeights.create_dummy_lora_weights(
                        module_name,
                        module.w13_input_size,
                        module.w13_output_size,
                        rank
                        * module.w13_lora_a_stacked[0].shape[1],  # rank*num_experts
                        module.w13_lora_a_stacked[0].dtype,
                        "cpu",
                    )
                    model.loras[module_name + ".base_layer"] = lora
                else:
                    lora = LoRALayerWeights.create_dummy_lora_weights(
                        module_name,
                        module.lora_a_stacked[0].shape[-1],
                        module.lora_b_stacked[0].shape[-2],
                        rank,
                        module.lora_a_stacked[0].dtype,
                        "cpu",
                    )
                    model.loras[module_name] = lora
            else:
                parts = module_name.split(".")
                replacements = self.packed_modules_mapping[parts[-1]]
                subloras: list[LoRALayerWeights | None] = []
                for i, r in enumerate(replacements):
                    lora = LoRALayerWeights.create_dummy_lora_weights(
                        module_name + "." + r,
                        module.lora_a_stacked[i].shape[-1],
                        module.lora_b_stacked[i].shape[-2],
                        rank,
                        module.lora_a_stacked[i].dtype,
                        "cpu",
                    )
                    subloras.append(lora)
                if module.__class__.__name__ == "FusedMoEWithLoRA":
                    # For non-gated MoE, pad subloras to 3 elements per expert
                    # to match pack_moe expectations (w1, w2, None for w3)
                    if self._is_non_gated_moe and len(subloras) > 0:
                        subloras = self._pad_lora_pairs_to_triplets(subloras)
                    lora = PackedLoRALayerWeights.pack_moe(
                        subloras, module_name, is_non_gated_moe=self._is_non_gated_moe
                    )
                else:
                    lora = PackedLoRALayerWeights.pack(subloras)
                model.loras[module_name] = lora
        return model