def _create_merged_loras_inplace(self, lora_model: LoRAModel) -> None:
        for module_name, new_module_names in self.packed_modules.items():
            replacement_loras: list[LoRALayerWeights | None] = []
            replaced_module: set[str] = set()
            has_replacement = False
            for r in new_module_names:
                lora = self._get_lora_layer_weights(lora_model, r)
                replacement_loras.append(lora)
                if lora:
                    has_replacement = True
                    replaced_module.add(r)
            if not has_replacement:
                continue
            for i in range(len(replacement_loras)):
                if replacement_loras[i]:
                    continue
                replacement_loras[i] = None
            # HACK Temporary solution for the pool model.
            if self.is_pooling_model and not lora_model.check_lora_name(module_name):
                replaced_module_name = module_name.removeprefix("model.")
                if lora_model.check_lora_name(replaced_module_name):
                    module_name = replaced_module_name
            if module_name.endswith(".experts"):
                if self._is_non_gated_moe and len(replacement_loras) > 0:
                    replacement_loras = self._pad_lora_pairs_to_triplets(
                        replacement_loras
                    )
                lora_model.loras[module_name] = PackedLoRALayerWeights.pack_moe(
                    replacement_loras,
                    module_name,
                    is_non_gated_moe=self._is_non_gated_moe,
                )
            else:
                lora_model.loras[module_name] = PackedLoRALayerWeights.pack(
                    replacement_loras
                )
            # Remove the modules that have been replaced.
            for module in replaced_module:
                lora_model.loras.pop(module, None)

        for lora in lora_model.loras.values():
            lora.optimize()

        for module_name, module in self.modules.items():
            if isinstance(module, FusedMoE3DWithLoRA):
                self._stack_moe_lora_weights(lora_model, module, module_name)

        first_lora: LoRALayerWeights = next(iter(lora_model.loras.values()))
        assert first_lora.lora_a is not None
        if isinstance(first_lora.lora_a, list):
            lora_device = next(iter(first_lora.lora_a))
        else:
            lora_device = first_lora.lora_a.device
        # Execute pin_memory after LoRA weight merging, mainly because:
        # 1. Some MoE models have a large number of LoRA weights. If we
        # perform # pin_memory immediately after loading weights, the
        # overhead is significant.
        # 2. The weight packing above (e.g., pack_moe) may invalidate the
        # pin_memory allocation, so we execute it after packing.

        pin_memory = str(lora_device) == "cpu" and is_pin_memory_available()
        if pin_memory:
            for lora in lora_model.loras.values():
                if isinstance(lora.lora_a, list):
                    for index in range(len(lora.lora_a)):
                        if lora.lora_a[index] is None:
                            continue
                        lora.lora_a[index] = lora.lora_a[index].pin_memory()
                        lora.lora_b[index] = lora.lora_b[index].pin_memory()
                else:
                    lora.lora_a = lora.lora_a.pin_memory()
                    lora.lora_b = lora.lora_b.pin_memory()