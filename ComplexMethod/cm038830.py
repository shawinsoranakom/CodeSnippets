def check_unexpected_modules(modules: dict):
            for lora_module in modules.keys():  # noqa
                if is_base_embedding_weights(lora_module):
                    continue
                # Handle PEFT file format where experts.base_layer is the
                # gate_up_proj and experts is the down_proj
                if "base_layer" in lora_module:
                    continue
                # Skip modules based on model-defined prefixes
                if skip_prefixes and cls._should_skip_module(
                    lora_module, skip_prefixes
                ):
                    continue
                module_name, _ = parse_fine_tuned_lora_name(lora_module, weights_mapper)
                # Case for expert lora weights
                if ".experts" in module_name:
                    expert_idx = module_name.find(".experts")
                    expert_suffix = module_name[expert_idx + 1 :]
                    if expert_suffix not in expected_lora_modules:
                        unexpected_modules.append(module_name)

                elif module_name.rsplit(".", 1)[-1] not in expected_lora_modules:
                    unexpected_modules.append(module_name)

            if unexpected_modules:
                raise ValueError(
                    f"While loading {lora_dir}, expected"
                    f" target modules in {expected_lora_modules}"
                    f" but received {unexpected_modules}."
                    f" Please verify that the loaded LoRA module is correct"
                )