def maybe_select_dummy_loras(
        self,
        lora_config: LoRAConfig | None,
        num_scheduled_tokens: np.ndarray,
        mapping_type: LoRAMappingType = LoRAMappingType.LANGUAGE,
        num_sampled_tokens: np.ndarray | None = None,
        num_active_loras: int = 0,
    ):
        """
        Context manager to select dummy LoRAs for capture/warmup.

        Args:
            lora_config: LoRA configuration, or None if LoRA is disabled.
            num_scheduled_tokens: Array of scheduled token counts per request.
            num_sampled_tokens: Array of sampled token counts per request.
            num_active_loras: Number of distinct active LoRAs to use.
                - 0: No LoRA active (set up zero mappings).
                - >0: Use exactly this many distinct LoRAs.
        """
        if num_sampled_tokens is None:
            num_sampled_tokens = np.ones_like(num_scheduled_tokens, dtype=np.int32)

        # Skip LoRA setup entirely only if no LoRA config
        if lora_config is None:
            yield
        else:
            # __enter__ code
            assert self.lora_manager is not None, "LoRA is not enabled"

            num_reqs = len(num_scheduled_tokens)
            max_loras = lora_config.max_loras

            # Determine how many distinct LoRAs to use and whether to include
            # no-LoRA tokens (-1 entries).
            # When num_active_loras > max_loras (e.g., max_loras + 1), we need
            # to include -1 entries to simulate batches with both LoRA and
            # no-LoRA tokens. This ensures prepare_tensors computes the correct
            # num_active_loras that matches the cudagraph capture key.
            if num_active_loras == 0:
                # No LoRA active - use 0 mappings like the original code
                effective_num_loras = 0
                include_no_lora = False
            elif num_active_loras > max_loras:
                # num_active_loras > max_loras means we want max_loras adapters
                # PLUS no-LoRA tokens (-1). This is the max_loras + 1 case.
                effective_num_loras = max_loras
                include_no_lora = True
            else:
                # Specific number of active LoRAs requested
                effective_num_loras = min(num_active_loras, max_loras)
                include_no_lora = False

            # Make prompt lora mapping
            # Assign LoRA IDs cyclically to simulate a worst-case scenario.
            # LoRA IDs are 1-indexed (1 to max_loras) as required by LoRARequest.
            # convert_mapping() will convert these to 0-indexed slot indices.
            if effective_num_loras > 0:
                if include_no_lora:
                    # Include -1 (no-LoRA) entries by cycling through
                    # -1, 1, 2, ..., effective_num_loras
                    # This ensures prepare_tensors sees both LoRA and no-LoRA
                    # tokens, computing num_active_loras = effective_num_loras+1
                    cycle_values = np.array(
                        list(range(1, effective_num_loras + 1)),
                        dtype=np.int32,
                    )
                    prompt_lora_mapping = cycle_values[
                        np.arange(num_reqs, dtype=np.int32) % len(cycle_values)
                    ]
                else:
                    # Use 1 to effective_num_loras (1-indexed lora IDs)
                    prompt_lora_mapping = (
                        np.arange(num_reqs, dtype=np.int32) % effective_num_loras
                    ) + 1
            else:
                # No LoRA active - use 0 for all tokens (original behavior)
                prompt_lora_mapping = np.zeros(num_reqs, dtype=np.int32)

            # Make sample lora mapping
            sample_lora_mapping = np.repeat(prompt_lora_mapping, num_sampled_tokens)

            # Make token lora mapping
            token_lora_mapping = np.repeat(prompt_lora_mapping, num_scheduled_tokens)

            # Make dummy lora requests (only for the active LoRAs)
            lora_requests: set[LoRARequest] = {
                LoRARequest(
                    lora_name=f"warmup_{lora_id}",
                    lora_int_id=lora_id,
                    lora_path="/not/a/real/path",
                )
                for lora_id in range(1, effective_num_loras + 1)
            }

            self._set_active_loras(
                tuple(sample_lora_mapping),
                tuple(token_lora_mapping),
                lora_requests,
                mapping_type,
            )

            yield