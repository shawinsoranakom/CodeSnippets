def prepare_model_for_training(
        self,
        use_lora: bool = True,
        # Vision-specific LoRA parameters (only used if is_vlm=True)
        finetune_vision_layers: bool = True,
        finetune_language_layers: bool = True,
        finetune_attention_modules: bool = True,
        finetune_mlp_modules: bool = True,
        # Standard LoRA parameters
        target_modules: list = None,
        lora_r: int = 16,
        lora_alpha: int = 16,
        lora_dropout: float = 0.0,
        use_gradient_checkpointing: str = "unsloth",
        use_rslora: bool = False,
        use_loftq: bool = False,
    ) -> bool:
        """
        Prepare model for training (with optional LoRA).
        """
        try:
            if self.model is None:
                raise ValueError("Model not loaded. Call load_model() first.")

            # Full finetuning mode - skip PEFT entirely
            if not use_lora:
                self._update_progress(
                    status_message = "Full finetuning mode - no LoRA adapters"
                )
                logger.info("Full finetuning mode - training all parameters\n")
                return True

            # LoRA/QLoRA mode - apply PEFT
            # "all-linear" is a PEFT keyword that targets every linear layer
            if isinstance(target_modules, list) and "all-linear" in target_modules:
                if len(target_modules) == 1:
                    target_modules = "all-linear"
                else:
                    target_modules = [m for m in target_modules if m != "all-linear"]
            elif target_modules is None or (
                isinstance(target_modules, list) and len(target_modules) == 0
            ):
                target_modules = [
                    "q_proj",
                    "k_proj",
                    "v_proj",
                    "o_proj",
                    "gate_proj",
                    "up_proj",
                    "down_proj",
                ]

            # Validate and normalize gradient_checkpointing
            # Must be one of: True, False, or "unsloth"
            if isinstance(use_gradient_checkpointing, str):
                use_gradient_checkpointing = use_gradient_checkpointing.strip().lower()
                if (
                    use_gradient_checkpointing == ""
                    or use_gradient_checkpointing == "unsloth"
                ):
                    use_gradient_checkpointing = "unsloth"
                elif use_gradient_checkpointing in ("true", "1", "yes"):
                    use_gradient_checkpointing = True
                elif use_gradient_checkpointing in ("false", "0", "no"):
                    use_gradient_checkpointing = False
                else:
                    # Invalid value, default to "unsloth"
                    logger.warning(
                        f"Invalid gradient_checkpointing value: {use_gradient_checkpointing}, defaulting to 'unsloth'"
                    )
                    use_gradient_checkpointing = "unsloth"
            elif use_gradient_checkpointing not in (True, False, "unsloth"):
                # Invalid type or value, default to "unsloth"
                logger.warning(
                    f"Invalid gradient_checkpointing type/value: {use_gradient_checkpointing}, defaulting to 'unsloth'"
                )
                use_gradient_checkpointing = "unsloth"

            # Verify model is loaded
            if self.model is None:
                error_msg = "Model is None - model was not loaded properly"
                logger.error(error_msg)
                self._update_progress(error = error_msg)
                return False

            # Check if model has the expected attributes
            if not hasattr(self.model, "config"):
                error_msg = "Model does not have config attribute - model may not be loaded correctly"
                logger.error(error_msg)
                self._update_progress(error = error_msg)
                return False

            logger.info(
                f"Configuring LoRA adapters (r={lora_r}, alpha={lora_alpha})...\n"
            )
            logger.info(
                f"Gradient checkpointing: {use_gradient_checkpointing} (type: {type(use_gradient_checkpointing).__name__})\n"
            )

            # Branch based on model type: audio, audio_vlm, vision, or text
            if self._audio_type in ("csm", "bicodec", "dac") or self.is_audio_vlm:
                # Models using FastModel.get_peft_model (codec audio + audio VLM)
                from unsloth import FastModel

                label = self._audio_type or "audio_vlm"
                logger.info(f"{label} LoRA configuration:")
                logger.info(f"  - Target modules: {target_modules}")
                if self.is_audio_vlm:
                    logger.info(f"  - Finetune vision layers: {finetune_vision_layers}")
                    logger.info(
                        f"  - Finetune language layers: {finetune_language_layers}"
                    )
                    logger.info(
                        f"  - Finetune attention modules: {finetune_attention_modules}"
                    )
                    logger.info(f"  - Finetune MLP modules: {finetune_mlp_modules}")
                logger.info()

                peft_kwargs = dict(
                    r = lora_r,
                    target_modules = target_modules,
                    lora_alpha = lora_alpha,
                    lora_dropout = lora_dropout,
                    bias = "none",
                    use_gradient_checkpointing = use_gradient_checkpointing,
                    random_state = 3407,
                    use_rslora = use_rslora,
                    loftq_config = {"loftq_bits": 4, "loftq_iter": 1}
                    if use_loftq
                    else None,
                )
                # Audio VLM models support VLM-style layer selection
                if self.is_audio_vlm:
                    peft_kwargs.update(
                        finetune_vision_layers = finetune_vision_layers,
                        finetune_language_layers = finetune_language_layers,
                        finetune_attention_modules = finetune_attention_modules,
                        finetune_mlp_modules = finetune_mlp_modules,
                    )

                self.model = FastModel.get_peft_model(self.model, **peft_kwargs)

            elif self._audio_type == "whisper":
                # Phase 2: Whisper uses FastModel.get_peft_model with task_type=None
                from unsloth import FastModel

                logger.info(f"Audio model (whisper) LoRA configuration:")
                logger.info(f"  - Target modules: {target_modules}\n")

                self.model = FastModel.get_peft_model(
                    self.model,
                    r = lora_r,
                    target_modules = target_modules,
                    lora_alpha = lora_alpha,
                    lora_dropout = lora_dropout,
                    bias = "none",
                    use_gradient_checkpointing = use_gradient_checkpointing,
                    random_state = 3407,
                    use_rslora = use_rslora,
                    loftq_config = {"loftq_bits": 4, "loftq_iter": 1}
                    if use_loftq
                    else None,
                    task_type = None,
                )

            elif self._audio_type == "snac":
                # Orpheus uses FastLanguageModel.get_peft_model
                logger.info(f"Audio model ({self._audio_type}) LoRA configuration:")
                logger.info(f"  - Target modules: {target_modules}\n")

                self.model = FastLanguageModel.get_peft_model(
                    self.model,
                    r = lora_r,
                    target_modules = target_modules,
                    lora_alpha = lora_alpha,
                    lora_dropout = lora_dropout,
                    bias = "none",
                    use_gradient_checkpointing = use_gradient_checkpointing,
                    random_state = 3407,
                    use_rslora = use_rslora,
                    loftq_config = {"loftq_bits": 4, "loftq_iter": 1}
                    if use_loftq
                    else None,
                )

            elif self.is_vlm:
                # Vision model LoRA
                logger.info(f"Vision model LoRA configuration:")
                logger.info(f"  - Finetune vision layers: {finetune_vision_layers}")
                logger.info(f"  - Finetune language layers: {finetune_language_layers}")
                logger.info(
                    f"  - Finetune attention modules: {finetune_attention_modules}"
                )
                logger.info(f"  - Finetune MLP modules: {finetune_mlp_modules}\n")

                self.model = FastVisionModel.get_peft_model(
                    self.model,
                    finetune_vision_layers = finetune_vision_layers,
                    finetune_language_layers = finetune_language_layers,
                    finetune_attention_modules = finetune_attention_modules,
                    finetune_mlp_modules = finetune_mlp_modules,
                    r = lora_r,
                    target_modules = target_modules,
                    lora_alpha = lora_alpha,
                    lora_dropout = lora_dropout,
                    bias = "none",
                    use_gradient_checkpointing = use_gradient_checkpointing,
                    random_state = 3407,
                    use_rslora = use_rslora,
                    loftq_config = {"loftq_bits": 4, "loftq_iter": 1}
                    if use_loftq
                    else None,
                )
            else:
                # Text model LoRA
                logger.info(f"Text model LoRA configuration:")
                logger.info(f"  - Target modules: {target_modules}\n")

                self.model = FastLanguageModel.get_peft_model(
                    self.model,
                    r = lora_r,
                    target_modules = target_modules,
                    lora_alpha = lora_alpha,
                    lora_dropout = lora_dropout,
                    bias = "none",
                    use_gradient_checkpointing = use_gradient_checkpointing,
                    random_state = 3407,
                    use_rslora = use_rslora,
                    loftq_config = {"loftq_bits": 4, "loftq_iter": 1}
                    if use_loftq
                    else None,
                )

            # Check if stopped during LoRA preparation
            if self.should_stop:
                logger.info("Stopped during LoRA configuration\n")
                return False

            self._update_progress(status_message = "LoRA adapters configured")
            logger.info("LoRA adapters configured successfully\n")
            return True

        except Exception as e:
            import traceback
            import sys

            error_details = (
                f"{type(e).__name__}: {str(e)}"
                if str(e)
                else f"{type(e).__name__} (no message)"
            )
            full_traceback = traceback.format_exc()
            logger.error(f"Error preparing model: {error_details}")
            logger.error(f"Full traceback:\n{full_traceback}")
            logger.info(f"\n[ERROR] Error preparing model: {error_details}")
            logger.info(f"[ERROR] Full traceback:\n{full_traceback}")
            self._update_progress(error = error_details)
            return False