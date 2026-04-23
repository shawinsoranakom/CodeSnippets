def _prepare_context_parallel_inputs(
        self, model: nn.Module, inputs: dict[str, torch.Tensor | Any]
    ) -> tuple[Callable, dict[str, torch.Tensor | Any]]:
        """
        Prepare inputs for context parallelism by setting up buffers and validation.

        Args:
            model: The model being trained
            inputs: Input tensors to prepare

        Returns:
            tuple: (context_manager, prepared_inputs) where context_manager is either
                   the context parallelism wrapper or a no-op context
        """
        if (
            getattr(self.accelerator, "parallelism_config", None) is not None
            and self.accelerator.parallelism_config.cp_enabled
        ):
            if self.accelerator.parallelism_config.cp_backend == "torch":
                if hasattr(model, "config"):
                    if model.config._attn_implementation != "sdpa":
                        raise ValueError(
                            f"Context parallelism is supported only with SDPA attention, you are using {model.config._attn_implementation}."
                        )

                if "shift_labels" not in inputs:
                    logger.warning_once("Shift labels not found in the inputs, shifting manually")
                    if "labels" in inputs:
                        _ignore_index = -100
                        labels = nn.functional.pad(inputs["labels"], (0, 1), value=_ignore_index)
                        inputs["shift_labels"] = labels[:, 1:].contiguous()

            # note: we don't do anything for accelerator.parallelism_config.sp_backend == "deepspeed" since:
            # - accelerator.parallelism_config performs the `model.config._attn_implementation` checks already and it supports more than `dspa`
            # - UlyssesSPDataLoaderAdapter called from Accelerate performs the `shift_label` creation - must not interfere
            # - position_ids generation should be done by HF Trainer if it wasn't done by the user

            if "position_ids" not in inputs:
                logger.warning_once("Position IDs not found in the inputs, generating manually")
                inputs["position_ids"] = torch.arange(
                    inputs["input_ids"].size(1), device=inputs["input_ids"].device
                ).expand(inputs["input_ids"].size(0), -1)

            buffers = []
            buffer_seq_dims = []

            if "input_ids" in inputs:
                buffers.append(inputs["input_ids"])
                buffer_seq_dims.append(1)  # Sequence dimension
            if "labels" in inputs:
                buffers.append(inputs["labels"])
                buffer_seq_dims.append(1)
            if "shift_labels" in inputs:
                buffers.append(inputs["shift_labels"])
                buffer_seq_dims.append(1)
            # Add attention_mask to buffers for context parallel splitting (only if causal)
            if "attention_mask" in inputs:
                # Only validate causal mask once for performance
                if not getattr(self, "_attn_mask_causal_checked", False):
                    # Context parallel currently doesn't support other masks than causal
                    # Accelerate applies hooks to replace mask with is_causal arg in SDPA
                    # Check if the mask is really causal and if not throw an error
                    attention_mask = inputs["attention_mask"]
                    if not is_attention_mask_causal(attention_mask):
                        raise ValueError(
                            "Context parallelism only supports causal attention masks. "
                            "The provided attention_mask is not causal. "
                            "Please ensure your data uses causal masking (lower triangular) "
                            "or remove the attention_mask to use the model's default causal masking."
                        )
                    self._attn_mask_causal_checked = True
                if self._attn_mask_causal_checked:
                    # Add to buffers only after validation (or if validation already passed)
                    attention_mask = inputs["attention_mask"]
                    if attention_mask.dim() == 2:
                        buffers.append(attention_mask)
                        buffer_seq_dims.append(1)
                    else:
                        # Other dimensionality; keep as-is without sharding to avoid incorrect splits
                        pass
            # Include position_ids in context parallelism splitting
            if "position_ids" in inputs and inputs["position_ids"] is not None:
                buffers.append(inputs["position_ids"])
                buffer_seq_dims.append(1)

            return partial(
                self.accelerator.maybe_context_parallel,
                buffers=buffers,
                buffer_seq_dims=buffer_seq_dims,
                no_restore_buffers=set(buffers),
            ), inputs

        return contextlib.nullcontext, inputs