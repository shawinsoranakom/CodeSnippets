def from_lora_tensors(
        cls,
        lora_model_id: int,
        tensors: dict[str, torch.Tensor],
        peft_helper: PEFTHelper,
        device: str = "cuda",
        dtype: torch.dtype | None = None,
        model_vocab_size: int | None = None,
        weights_mapper: WeightsMapper | None = None,
        skip_prefixes: list[str] | None = None,
    ) -> "LoRAModel":
        """Create a LoRAModel from a dictionary of tensors."""
        pin_memory = str(device) == "cpu" and is_pin_memory_available()
        loras: dict[str, LoRALayerWeights] = {}
        for tensor_name, tensor in tensors.items():
            if is_base_embedding_weights(tensor_name):
                continue
            # Skip modules based on model-defined prefixes (e.g., MTP layers)
            if skip_prefixes and cls._should_skip_module(tensor_name, skip_prefixes):
                continue
            module_name, is_lora_a = parse_fine_tuned_lora_name(
                tensor_name, weights_mapper
            )
            if module_name not in loras:
                loras[module_name] = LoRALayerWeights.from_config(
                    module_name, peft_helper
                )

            if is_lora_a:
                if (
                    "lora_embedding_A" in tensor_name
                    and model_vocab_size is not None
                    and model_vocab_size != tensor.shape[1]
                ):
                    raise RuntimeError(
                        f"The embedding LoRA size({tensor.shape[1]}) must be consistent"
                        f" with the base model's vocabulary size({model_vocab_size})."
                    )
                loras[module_name].lora_a = tensor.to(device=device, dtype=dtype)
                if pin_memory:
                    loras[module_name].lora_a = loras[module_name].lora_a.pin_memory()
            else:
                loras[module_name].lora_b = tensor.to(device=device, dtype=dtype)

                if pin_memory:
                    loras[module_name].lora_b = loras[module_name].lora_b.pin_memory()

        return cls(lora_model_id, peft_helper.r, loras)