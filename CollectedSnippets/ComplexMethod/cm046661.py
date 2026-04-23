def load_model(
        self,
        config: ModelConfig,
        max_seq_length: int = 2048,
        dtype = None,
        load_in_4bit: bool = True,
        hf_token: Optional[str] = None,
        trust_remote_code: bool = False,
        gpu_ids: Optional[list[int]] = None,
    ) -> bool:
        """
        Load any model: base, LoRA adapter, text, or vision.
        """
        # GGUF uses max_seq_length=0 as "model default"; Unsloth crashes on it.
        if max_seq_length <= 0:
            max_seq_length = 2048

        try:
            model_name = config.identifier

            # Check if already loaded
            if model_name in self.models and self.models[model_name].get("model"):
                logger.info(f"Model {model_name} already loaded")
                self.active_model_name = model_name
                return True

            # Check if currently loading
            if model_name in self.loading_models:
                logger.info(f"Model {model_name} is already being loaded")
                return False

            self.loading_models.add(model_name)
            device_map = get_device_map(gpu_ids)
            logger.info(
                f"Using device_map='{device_map}' ({get_visible_gpu_count()} GPU(s) visible)"
            )

            self.models[model_name] = {
                "is_vision": config.is_vision,
                "is_lora": config.is_lora,
                "is_audio": config.is_audio,
                "audio_type": config.audio_type,
                "has_audio_input": config.has_audio_input,
                "model_path": config.path,
                "base_model": config.base_model if config.is_lora else None,
                "loaded_adapters": {},
                "active_adapter": None,
            }

            # ── Audio model loading path ──────────────────────────
            if config.is_audio:
                audio_type = config.audio_type
                adapter_info = " (LoRA adapter)" if config.is_lora else ""
                logger.info(
                    f"Loading audio ({audio_type}) model{adapter_info}: {model_name}"
                )
                log_gpu_memory(f"Before loading {model_name}")

                if audio_type == "csm":
                    from unsloth import FastModel
                    from transformers import CsmForConditionalGeneration

                    model, processor = FastModel.from_pretrained(
                        config.path,
                        auto_model = CsmForConditionalGeneration,
                        load_in_4bit = False,
                        device_map = device_map,
                        token = hf_token if hf_token and hf_token.strip() else None,
                        trust_remote_code = trust_remote_code,
                    )
                    FastModel.for_inference(model)
                    self.models[model_name]["model"] = model
                    self.models[model_name]["tokenizer"] = processor
                    self.models[model_name]["processor"] = processor
                elif audio_type == "bicodec":
                    import os
                    from unsloth import FastModel

                    if config.is_lora and config.base_model:
                        # LoRA adapter: load from local adapter path.
                        # base_model is e.g. /home/.../Spark-TTS-0.5B/LLM
                        # The BiCodec weights are in the parent dir (Spark-TTS-0.5B/).
                        base_path = config.base_model
                        if os.path.isdir(base_path):
                            abs_repo_path = os.path.abspath(os.path.dirname(base_path))
                        else:
                            # base_model is an HF ID — download it
                            from huggingface_hub import snapshot_download

                            local_dir = base_path.split("/")[-1]
                            repo_path = snapshot_download(
                                base_path, local_dir = local_dir
                            )
                            abs_repo_path = os.path.abspath(repo_path)

                        logger.info(
                            f"Spark-TTS LoRA: loading adapter from {config.path}, BiCodec from {abs_repo_path}"
                        )
                        model, tokenizer = FastModel.from_pretrained(
                            config.path,
                            dtype = torch.float32,
                            load_in_4bit = False,
                            device_map = device_map,
                            token = hf_token if hf_token and hf_token.strip() else None,
                            trust_remote_code = trust_remote_code,
                        )
                    else:
                        # Base model: download full HF repo, then load from /LLM subfolder
                        from huggingface_hub import snapshot_download

                        hf_repo = config.path
                        local_dir = hf_repo.split("/")[-1]
                        repo_path = snapshot_download(hf_repo, local_dir = local_dir)
                        abs_repo_path = os.path.abspath(repo_path)
                        llm_path = os.path.join(abs_repo_path, "LLM")
                        logger.info(
                            f"Spark-TTS: downloaded repo to {repo_path}, loading LLM from {llm_path}"
                        )

                        model, tokenizer = FastModel.from_pretrained(
                            llm_path,
                            dtype = torch.float32,
                            load_in_4bit = False,
                            device_map = device_map,
                            token = hf_token if hf_token and hf_token.strip() else None,
                            trust_remote_code = trust_remote_code,
                        )

                    FastModel.for_inference(model)
                    self.models[model_name]["model"] = model
                    self.models[model_name]["tokenizer"] = tokenizer
                    self.models[model_name]["model_repo_path"] = abs_repo_path
                elif audio_type == "dac":
                    # OuteTTS uses FastModel (not FastLanguageModel)
                    from unsloth import FastModel

                    model, tokenizer = FastModel.from_pretrained(
                        config.path,
                        max_seq_length = max_seq_length,
                        load_in_4bit = False,
                        device_map = device_map,
                        token = hf_token if hf_token and hf_token.strip() else None,
                        trust_remote_code = trust_remote_code,
                    )
                    FastModel.for_inference(model)
                    self.models[model_name]["model"] = model
                    self.models[model_name]["tokenizer"] = tokenizer
                elif audio_type == "whisper":
                    # Whisper ASR — uses FastModel with WhisperForConditionalGeneration
                    from unsloth import FastModel
                    from transformers import WhisperForConditionalGeneration

                    model, tokenizer = FastModel.from_pretrained(
                        config.path,
                        auto_model = WhisperForConditionalGeneration,
                        whisper_language = "English",
                        whisper_task = "transcribe",
                        load_in_4bit = False,
                        device_map = device_map,
                        token = hf_token if hf_token and hf_token.strip() else None,
                        trust_remote_code = trust_remote_code,
                    )
                    FastModel.for_inference(model)
                    model.eval()

                    # Create ASR pipeline (per notebook)
                    from transformers import pipeline as hf_pipeline

                    whisper_pipe = hf_pipeline(
                        "automatic-speech-recognition",
                        model = model,
                        tokenizer = tokenizer.tokenizer,
                        feature_extractor = tokenizer.feature_extractor,
                        processor = tokenizer,
                        return_language = True,
                        torch_dtype = torch.float16,
                    )
                    self.models[model_name]["model"] = model
                    self.models[model_name]["tokenizer"] = tokenizer
                    self.models[model_name]["whisper_pipeline"] = whisper_pipe
                else:
                    # SNAC (Orpheus) uses FastLanguageModel
                    model, tokenizer = FastLanguageModel.from_pretrained(
                        model_name = config.path,
                        max_seq_length = max_seq_length,
                        load_in_4bit = False,
                        device_map = device_map,
                        token = hf_token if hf_token and hf_token.strip() else None,
                        trust_remote_code = trust_remote_code,
                    )
                    FastLanguageModel.for_inference(model)
                    self.models[model_name]["model"] = model
                    self.models[model_name]["tokenizer"] = tokenizer

                # Load the external codec for TTS audio types
                # (Whisper is ASR, audio_vlm is audio input — neither needs a codec)
                if audio_type not in ("whisper", "audio_vlm"):
                    model_repo_path = self.models[model_name].get("model_repo_path")
                    self._audio_codec_manager.load_codec(
                        audio_type, self.device, model_repo_path = model_repo_path
                    )

                # Reject CPU/disk offload for audio models too
                raise_if_offloaded(
                    self.models[model_name]["model"], device_map, "Inference"
                )

                self.active_model_name = model_name
                self.loading_models.discard(model_name)
                logger.info(f"Successfully loaded audio model: {model_name}")
                log_gpu_memory(f"After loading {model_name}")
                return True

            model_type = "vision" if config.is_vision else "text"
            adapter_info = (
                " (LoRA adapter)" if self.models[model_name]["is_lora"] else ""
            )
            logger.info(f"Loading {model_type} model{adapter_info}: {model_name}")
            log_gpu_memory(f"Before loading {model_name}")

            # Load model - same approach for base models and LoRA adapters
            if config.is_vision:
                # Vision model (or vision LoRA adapter)
                model, processor = FastVisionModel.from_pretrained(
                    model_name = config.path,  # Can be base model OR LoRA adapter path
                    max_seq_length = max_seq_length,
                    dtype = dtype,
                    load_in_4bit = load_in_4bit,
                    device_map = device_map,
                    token = hf_token if hf_token and hf_token.strip() else None,
                    trust_remote_code = trust_remote_code,
                )

                # Apply inference optimization
                FastVisionModel.for_inference(model)

                # FastVisionModel may return a raw tokenizer (e.g. GemmaTokenizerFast)
                # instead of a proper Processor for some models (e.g. Gemma-3).
                # In that case, load the real processor from the base model.
                from transformers import ProcessorMixin

                if not (
                    isinstance(processor, ProcessorMixin)
                    or hasattr(processor, "image_processor")
                ):
                    # For LoRA adapters, use the base model. For local merged exports,
                    # read export_metadata.json to find the original base model.
                    processor_source = (
                        config.base_model if config.is_lora else config.identifier
                    )
                    if not config.is_lora and config.is_local:
                        _meta_path = Path(config.path) / "export_metadata.json"
                        try:
                            if _meta_path.exists():
                                _meta = json.loads(_meta_path.read_text())
                                if _meta.get("base_model"):
                                    processor_source = _meta["base_model"]
                        except Exception:
                            pass
                    logger.warning(
                        f"FastVisionModel returned {type(processor).__name__} (no image_processor) "
                        f"for '{model_name}' — loading proper processor from '{processor_source}'"
                    )
                    from transformers import AutoProcessor

                    processor = AutoProcessor.from_pretrained(
                        processor_source,
                        token = hf_token if hf_token and hf_token.strip() else None,
                        trust_remote_code = trust_remote_code,
                    )
                    logger.info(
                        f"Loaded {type(processor).__name__} from {processor_source}"
                    )

                self.models[model_name]["model"] = model
                self.models[model_name]["tokenizer"] = processor
                self.models[model_name]["processor"] = processor

            else:
                # Text model (or text LoRA adapter)
                model, tokenizer = FastLanguageModel.from_pretrained(
                    model_name = config.path,  # Can be base model OR LoRA adapter path
                    max_seq_length = max_seq_length,
                    dtype = dtype,
                    load_in_4bit = load_in_4bit,
                    device_map = device_map,
                    token = hf_token if hf_token and hf_token.strip() else None,
                    trust_remote_code = trust_remote_code,
                )

                # Apply inference optimization
                FastLanguageModel.for_inference(model)

                self.models[model_name]["model"] = model
                self.models[model_name]["tokenizer"] = tokenizer

            raise_if_offloaded(
                self.models[model_name]["model"], device_map, "Inference"
            )

            # Load chat template info
            self._load_chat_template_info(model_name)

            self.active_model_name = model_name
            self.loading_models.discard(model_name)

            logger.info(f"Successfully loaded model: {model_name}")
            log_gpu_memory(f"After loading {model_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            error_msg = format_error_message(e, config.identifier)

            # Cleanup on failure
            if model_name in self.models:
                del self.models[model_name]
            self.loading_models.discard(model_name)

            raise Exception(error_msg)