def _load_adapter(self, lora_request: LoRARequest) -> LoRAModel:
        try:
            supported_lora_modules = self._adapter_manager.supported_lora_modules
            packed_modules_mapping = self._adapter_manager.packed_modules_mapping
            expected_lora_lst: list[str] = []
            for module in supported_lora_modules:
                if module in packed_modules_mapping:
                    expected_lora_lst.extend(packed_modules_mapping[module])
                else:
                    expected_lora_lst.append(module)
                if module == "experts":
                    expected_lora_lst.append(module)
            expected_lora_modules = set(expected_lora_lst)
            lora_path = get_adapter_absolute_path(lora_request.lora_path)

            peft_helper = PEFTHelper.from_local_dir(
                lora_path,
                self.max_position_embeddings,
                lora_request.tensorizer_config_dict,
            )

            # Validates the LoRA configuration against requirements before
            # loading weights, throwing an exception if validation fails.
            peft_helper.validate_legal(self.lora_config)

            # For some models like Qwen2VL, we need to use hf_to_vllm_mapper
            # to ensure correct loading of lora weights.
            model = self._adapter_manager.model
            hf_to_vllm_mapper = getattr(model, "hf_to_vllm_mapper", None)

            # Get model-defined prefixes to skip during LoRA loading.
            lora_skip_prefixes = getattr(model, "lora_skip_prefixes", None)

            lora = self._lora_model_cls.from_local_checkpoint(
                lora_path,
                expected_lora_modules,
                peft_helper=peft_helper,
                lora_model_id=lora_request.lora_int_id,
                device="cpu",
                dtype=self.lora_config.lora_dtype,
                model_vocab_size=self.vocab_size,
                tensorizer_config_dict=lora_request.tensorizer_config_dict,
                weights_mapper=hf_to_vllm_mapper,
                skip_prefixes=lora_skip_prefixes,
            )

            # Warn about adapter modules that will be ignored.
            target_modules = self.lora_config.target_modules
            expected_lora_modules_lst = list(expected_lora_modules)
            for module_name in lora.loras:
                if not is_supported_lora_module(module_name, expected_lora_modules_lst):
                    logger.warning_once(
                        "LoRA module '%s' in adapter '%s' is not in the "
                        "model's supported LoRA target modules [%s]. "
                        "These parameters will be ignored, which may "
                        "cause abnormal model behavior.",
                        module_name,
                        lora_request.lora_path,
                        ", ".join(sorted(expected_lora_modules_lst)),
                    )
                elif not is_in_target_modules(
                    module_name,
                    target_modules,
                    packed_modules_mapping,
                ):
                    logger.warning_once(
                        "LoRA module '%s' in adapter '%s' is not in the "
                        "deployment-time target_modules restriction [%s]."
                        " These parameters will be ignored.",
                        module_name,
                        lora_request.lora_path,
                        ", ".join(sorted(target_modules)),
                    )

        except FileNotFoundError as e:
            # FileNotFoundError should be raised if both
            # - No adapter found to download from huggingface (or in
            #       offline mode)
            # - No local adapter files found at `lora_request.lora_path`
            # For NotFoundError
            raise LoRAAdapterNotFoundError(
                lora_request.lora_name, lora_request.lora_path
            ) from e
        except Exception as e:
            raise e

        return lora