def _resolve_mm_lora(
        self,
        prompt: EngineInput,
        lora_request: LoRARequest | None,
    ) -> LoRARequest | None:
        if prompt["type"] != "multimodal":
            return lora_request

        lora_config = self.llm_engine.vllm_config.lora_config
        default_mm_loras = None if lora_config is None else lora_config.default_mm_loras
        if not default_mm_loras:
            return lora_request

        prompt_modalities = prompt["mm_placeholders"].keys()
        intersection = set(prompt_modalities).intersection(default_mm_loras.keys())
        if not intersection:
            return lora_request

        if len(intersection) > 1:
            # TODO: Would be nice to be able to have multiple loras per prompt
            logger.warning(
                "Multiple modality specific loras were registered and would be "
                "used by a single prompt consuming several modalities; "
                "currently we only support one lora per request; as such, "
                "lora(s) registered with modalities: %s will be skipped",
                intersection,
            )
            return lora_request

        # Build the LoRA request; the ID of the default mm lora is the
        # index of the modality name sorted alphabetically + 1.
        modality_name = intersection.pop()
        modality_lora_path = default_mm_loras[modality_name]
        modality_lora_id = sorted(default_mm_loras).index(modality_name) + 1

        # If we have a collision, warn if there is a collision,
        # but always send the explicitly provided request.
        if lora_request:
            if lora_request.lora_int_id != modality_lora_id:
                logger.warning(
                    "A modality with a registered lora and a lora_request "
                    "with a different ID were provided; falling back to the "
                    "lora_request as we only apply one LoRARequest per prompt"
                )
            return lora_request

        return LoRARequest(
            modality_name,
            modality_lora_id,
            modality_lora_path,
        )