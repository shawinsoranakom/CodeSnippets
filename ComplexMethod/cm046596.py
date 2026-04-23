def load_checkpoint(
        self,
        checkpoint_path: str,
        max_seq_length: int = 2048,
        load_in_4bit: bool = True,
        trust_remote_code: bool = False,
    ) -> Tuple[bool, str]:
        """
        Load a checkpoint for export.

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            logger.info(f"Loading checkpoint: {checkpoint_path}")

            # First, cleanup existing models
            self.cleanup_memory()

            checkpoint_path_obj = Path(checkpoint_path)

            # Determine the model identity for type detection
            adapter_config = checkpoint_path_obj / "adapter_config.json"
            base_model = None
            if adapter_config.exists():
                base_model = get_base_model_from_lora(checkpoint_path)
                if not base_model:
                    return False, "Could not determine base model for adapter"

            model_id = base_model or checkpoint_path

            # Detect audio type and vision
            self._audio_type = detect_audio_type(model_id)
            self.is_vision = not self._audio_type and is_vision_model(model_id)

            # Load model based on type
            if self._audio_type == "csm":
                from unsloth import FastModel
                from transformers import CsmForConditionalGeneration

                logger.info("Loading as CSM audio model...")
                model, tokenizer = FastModel.from_pretrained(
                    model_name = checkpoint_path,
                    max_seq_length = max_seq_length,
                    dtype = None,
                    auto_model = CsmForConditionalGeneration,
                    load_in_4bit = False,
                    trust_remote_code = trust_remote_code,
                )

            elif self._audio_type == "whisper":
                from unsloth import FastModel
                from transformers import WhisperForConditionalGeneration

                logger.info("Loading as Whisper audio model...")
                model, tokenizer = FastModel.from_pretrained(
                    model_name = checkpoint_path,
                    dtype = None,
                    load_in_4bit = False,
                    auto_model = WhisperForConditionalGeneration,
                    trust_remote_code = trust_remote_code,
                )

            elif self._audio_type == "snac":
                logger.info("Loading as SNAC (Orpheus) audio model...")
                model, tokenizer = FastLanguageModel.from_pretrained(
                    model_name = checkpoint_path,
                    max_seq_length = max_seq_length,
                    dtype = None,
                    load_in_4bit = load_in_4bit,
                    trust_remote_code = trust_remote_code,
                )

            elif self._audio_type == "bicodec":
                from unsloth import FastModel

                logger.info("Loading as BiCodec (Spark-TTS) audio model...")
                model, tokenizer = FastModel.from_pretrained(
                    model_name = checkpoint_path,
                    max_seq_length = max_seq_length,
                    dtype = torch.float32,
                    load_in_4bit = False,
                    trust_remote_code = trust_remote_code,
                )

            elif self._audio_type == "dac":
                from unsloth import FastModel

                logger.info("Loading as DAC (OuteTTS) audio model...")
                model, tokenizer = FastModel.from_pretrained(
                    model_name = checkpoint_path,
                    max_seq_length = max_seq_length,
                    load_in_4bit = False,
                    trust_remote_code = trust_remote_code,
                )

            elif self.is_vision:
                logger.info("Loading as vision model...")
                model, processor = FastVisionModel.from_pretrained(
                    model_name = checkpoint_path,
                    max_seq_length = max_seq_length,
                    dtype = None,
                    load_in_4bit = load_in_4bit,
                    trust_remote_code = trust_remote_code,
                )
                tokenizer = processor  # For vision models, processor acts as tokenizer

            else:
                logger.info("Loading as text model...")
                model, tokenizer = FastLanguageModel.from_pretrained(
                    model_name = checkpoint_path,
                    max_seq_length = max_seq_length,
                    dtype = None,
                    load_in_4bit = load_in_4bit,
                    trust_remote_code = trust_remote_code,
                )

            # Check if PEFT model
            self.is_peft = isinstance(model, (PeftModel, PeftModelForCausalLM))

            # Store loaded model
            self.current_model = model
            self.current_tokenizer = tokenizer
            self.current_checkpoint = checkpoint_path

            if self._audio_type:
                model_type = f"Audio ({self._audio_type})"
            elif self.is_vision:
                model_type = "Vision"
            else:
                model_type = "Text"
            peft_info = " (PEFT Adapter)" if self.is_peft else " (Merged Model)"

            logger.info(f"Successfully loaded {model_type} model{peft_info}")
            return True, f"Loaded {model_type} model{peft_info} successfully"

        except Exception as e:
            logger.error(f"Error loading checkpoint: {e}")
            import traceback

            logger.error(traceback.format_exc())
            return False, f"Failed to load checkpoint: {str(e)}"