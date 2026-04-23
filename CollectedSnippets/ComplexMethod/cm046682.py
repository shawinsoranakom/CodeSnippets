def load_model(
        self,
        model_name: str,
        max_seq_length: int = 2048,
        load_in_4bit: bool = True,
        hf_token: Optional[str] = None,
        is_dataset_image: bool = False,
        is_dataset_audio: bool = False,
        trust_remote_code: bool = False,
        full_finetuning: bool = False,
        gpu_ids: Optional[list[int]] = None,
    ) -> bool:
        """Load model for training (supports both text and vision models)"""
        self.load_in_4bit = load_in_4bit  # Store for training_meta.json
        self.trust_remote_code = (
            trust_remote_code  # For AutoProcessor etc. used during training
        )
        try:
            if self.model is not None:
                del self.model
            if self.tokenizer is not None:
                del self.tokenizer

            if self.trainer is not None:
                del self.trainer

            logger.info("\nClearing GPU memory before training...")
            clear_gpu_cache()

            # Clean up sys.path and sys.modules from previous audio preprocessing
            # to prevent deadlocks when forking worker processes in dataset.map()
            self._cleanup_audio_artifacts()

            # Reload Unsloth-patched transformers modeling modules before clearing
            # the compiled cache. unsloth_compile_transformers() sets __UNSLOTH_PATCHED__
            # on each modeling module and replaces methods with exec'd code.
            # clear_unsloth_compiled_cache() deletes the disk cache, but the flag
            # prevents re-compilation — leaving missing cache files. Reloading
            # restores original class definitions so Unsloth can re-compile cleanly.
            import sys as _sys
            import importlib

            for _key, _mod in list(_sys.modules.items()):
                if "transformers.models." in _key and ".modeling_" in _key:
                    if hasattr(_mod, "__UNSLOTH_PATCHED__"):
                        try:
                            importlib.reload(_mod)
                        except Exception:
                            pass  # Non-critical — Unsloth will handle stale modules

            # Remove stale compiled cache so the new model gets a fresh one
            from utils.cache_cleanup import clear_unsloth_compiled_cache

            _preserve = (
                ["Unsloth*Trainer.py"] if sys.platform in ("win32", "darwin") else None
            )
            clear_unsloth_compiled_cache(preserve_patterns = _preserve)
            # Detect audio model type dynamically (config.json + tokenizer)
            self._audio_type = detect_audio_type(model_name, hf_token)
            # audio_vlm is detected as an audio_type now, handle it separately
            if self._audio_type == "audio_vlm":
                self.is_audio = False
                self.is_audio_vlm = (
                    is_dataset_audio  # Only use audio VLM path if dataset has audio
                )
                self._audio_type = None
            else:
                self.is_audio = self._audio_type is not None
                self.is_audio_vlm = False

            if not self.is_audio and not self.is_audio_vlm:
                self._cuda_audio_used = False

            # VLM: vision model with image dataset (mutually exclusive with audio paths)
            vision = (
                is_vision_model(model_name, hf_token = hf_token)
                if not self.is_audio
                else False
            )
            self.is_vlm = not self.is_audio_vlm and vision and is_dataset_image
            self.model_name = model_name
            self.max_seq_length = max_seq_length

            logger.info(
                f"Audio type: {self._audio_type}, is_audio: {self.is_audio}, is_audio_vlm: {self.is_audio_vlm}"
            )
            logger.info(
                f"Dataset has images: {is_dataset_image}, audio: {is_dataset_audio}"
            )
            logger.info(f"Using VLM path: {self.is_vlm}")

            # Reset training state for new run
            self._update_progress(
                is_training = True,
                is_completed = False,
                error = None,
                step = 0,
                loss = 0.0,
                epoch = 0,
            )

            # Update UI immediately with loading message
            model_display = (
                model_name.split("/")[-1] if "/" in model_name else model_name
            )
            model_type_label = (
                "audio" if self.is_audio else ("vision" if self.is_vlm else "text")
            )
            self._update_progress(
                status_message = f"Loading {model_type_label} model... {model_display}"
            )

            logger.info(f"\nLoading {model_type_label} model: {model_name}")

            # Set HF token if provided
            if hf_token:
                os.environ["HF_TOKEN"] = hf_token

            # Proactive gated-model check: verify access BEFORE from_pretrained.
            # Catches ALL gated/private models (text, vision, audio) globally.
            if "/" in model_name:  # Only check HF repo IDs, not local paths
                try:
                    from huggingface_hub import model_info as hf_model_info

                    info = hf_model_info(model_name, token = hf_token or None)
                    # model_info succeeds even for gated repos (metadata is public),
                    # but info.gated tells us if files require acceptance/token.
                    if info.gated and not hf_token:
                        friendly = (
                            f"Access denied for '{model_name}'. This model is gated. "
                            f"Please add a Hugging Face token with access and try again."
                        )
                        logger.error(
                            f"Model '{model_name}' is gated (gated={info.gated}) and no HF token provided"
                        )
                        self._update_progress(error = friendly, is_training = False)
                        return False
                except Exception as gate_err:
                    from huggingface_hub.utils import (
                        GatedRepoError,
                        RepositoryNotFoundError,
                    )

                    if isinstance(gate_err, (GatedRepoError, RepositoryNotFoundError)):
                        friendly = (
                            f"Access denied for '{model_name}'. This model is gated or private. "
                            f"Please add a Hugging Face token with access and try again."
                        )
                        logger.error(f"Gated model check failed: {gate_err}")
                        self._update_progress(error = friendly, is_training = False)
                        return False

            device_map = get_device_map(gpu_ids)
            logger.info(
                f"Using device_map='{device_map}' ({get_visible_gpu_count()} GPU(s) visible)"
            )

            # Branch based on model type
            if self._audio_type == "csm":
                # CSM: FastModel + auto_model=CsmForConditionalGeneration + load_in_4bit=False
                from unsloth import FastModel
                from transformers import CsmForConditionalGeneration

                self.model, self.tokenizer = FastModel.from_pretrained(
                    model_name = model_name,
                    max_seq_length = max_seq_length,
                    dtype = None,
                    auto_model = CsmForConditionalGeneration,
                    load_in_4bit = False,
                    device_map = device_map,
                    full_finetuning = full_finetuning,
                    token = hf_token,
                    trust_remote_code = trust_remote_code,
                )
                logger.info("Loaded CSM audio model")

            elif self._audio_type == "whisper":
                # Whisper: FastModel + auto_model=WhisperForConditionalGeneration + load_in_4bit=False
                from unsloth import FastModel
                from transformers import WhisperForConditionalGeneration

                self.model, self.tokenizer = FastModel.from_pretrained(
                    model_name = model_name,
                    dtype = None,
                    load_in_4bit = False,
                    device_map = device_map,
                    full_finetuning = full_finetuning,
                    auto_model = WhisperForConditionalGeneration,
                    whisper_language = "English",
                    whisper_task = "transcribe",
                    token = hf_token,
                    trust_remote_code = trust_remote_code,
                )
                # Configure generation settings (notebook lines 100-105)
                self.model.generation_config.language = "<|en|>"
                self.model.generation_config.task = "transcribe"
                self.model.config.suppress_tokens = []
                self.model.generation_config.forced_decoder_ids = None
                logger.info("Loaded Whisper audio model (FastModel)")

            elif self._audio_type == "snac":
                # Orpheus: language model with audio codec tokens
                self.model, self.tokenizer = FastLanguageModel.from_pretrained(
                    model_name = model_name,
                    max_seq_length = max_seq_length,
                    dtype = None,
                    load_in_4bit = load_in_4bit,
                    device_map = device_map,
                    full_finetuning = full_finetuning,
                    token = hf_token,
                    trust_remote_code = trust_remote_code,
                )
                logger.info(
                    f"Loaded {self._audio_type} audio model (FastLanguageModel)"
                )

            elif self._audio_type == "bicodec":
                # Spark-TTS: download full repo (contains sparktts package + BiCodec weights),
                # then load only the LLM subfolder with FastModel.
                # model_name may be:
                #   "Spark-TTS-0.5B/LLM"       (local-style, from YAML mapping)
                #   "unsloth/Spark-TTS-0.5B"    (HF repo ID)
                from unsloth import FastModel
                from huggingface_hub import snapshot_download

                if model_name.endswith("/LLM"):
                    # "Spark-TTS-0.5B/LLM" → parent="Spark-TTS-0.5B"
                    local_dir = model_name.rsplit("/", 1)[0]
                    hf_repo = f"unsloth/{local_dir}"
                    llm_path = model_name
                else:
                    # "unsloth/Spark-TTS-0.5B" → local_dir="Spark-TTS-0.5B"
                    hf_repo = model_name
                    local_dir = model_name.split("/")[-1]
                    llm_path = f"{local_dir}/LLM"

                repo_path = snapshot_download(hf_repo, local_dir = local_dir)
                self._spark_tts_repo_dir = os.path.abspath(
                    repo_path
                )  # Absolute path for sys.path
                llm_path = os.path.join(self._spark_tts_repo_dir, "LLM")

                self.model, self.tokenizer = FastModel.from_pretrained(
                    model_name = llm_path,
                    max_seq_length = max_seq_length,
                    dtype = torch.float32,  # Spark-TTS requires float32
                    load_in_4bit = False,
                    device_map = device_map,
                    full_finetuning = full_finetuning,
                    token = hf_token,
                    trust_remote_code = trust_remote_code,
                )
                logger.info("Loaded Spark-TTS (bicodec) model")

            elif self._audio_type == "dac":
                # OuteTTS: uses FastModel (not FastLanguageModel) with load_in_4bit=False
                from unsloth import FastModel

                self.model, self.tokenizer = FastModel.from_pretrained(
                    model_name,
                    max_seq_length = max_seq_length,
                    load_in_4bit = False,
                    device_map = device_map,
                    full_finetuning = full_finetuning,
                    token = hf_token,
                    trust_remote_code = trust_remote_code,
                )
                logger.info("Loaded OuteTTS (dac) model (FastModel)")

            elif self.is_audio_vlm:
                # Audio VLM: multimodal model trained on audio (e.g. Gemma 3N)
                # Uses FastModel (general loader) — returns (model, processor)
                from unsloth import FastModel

                self.model, self.tokenizer = FastModel.from_pretrained(
                    model_name = model_name,
                    max_seq_length = max_seq_length,
                    dtype = None,
                    load_in_4bit = load_in_4bit,
                    device_map = device_map,
                    full_finetuning = full_finetuning,
                    token = hf_token,
                    trust_remote_code = trust_remote_code,
                )
                logger.info("Loaded audio VLM model (FastModel)")

            elif self.is_vlm:
                # Load vision model - returns (model, tokenizer)
                self.model, self.tokenizer = FastVisionModel.from_pretrained(
                    model_name = model_name,
                    max_seq_length = max_seq_length,
                    dtype = None,  # Auto-detect
                    load_in_4bit = load_in_4bit,
                    device_map = device_map,
                    full_finetuning = full_finetuning,
                    token = hf_token,
                    trust_remote_code = trust_remote_code,
                )
                logger.info("Loaded vision model")

                # Diagnostic: check if FastVisionModel returned a real Processor or a raw tokenizer
                from transformers import ProcessorMixin

                tok = self.tokenizer
                has_image_proc = isinstance(tok, ProcessorMixin) or hasattr(
                    tok, "image_processor"
                )
                logger.info(
                    f"\n[VLM Diagnostic] FastVisionModel returned: {type(tok).__name__}"
                )
                logger.info(
                    f"[VLM Diagnostic] Is ProcessorMixin: {isinstance(tok, ProcessorMixin)}"
                )
                logger.info(
                    f"[VLM Diagnostic] Has image_processor: {hasattr(tok, 'image_processor')}"
                )
                logger.info(
                    f"[VLM Diagnostic] Usable as vision processor: {has_image_proc}\n"
                )
            else:
                # Load text model - returns (model, tokenizer)
                self.model, self.tokenizer = FastLanguageModel.from_pretrained(
                    model_name = model_name,
                    max_seq_length = max_seq_length,
                    dtype = None,  # Auto-detect
                    load_in_4bit = load_in_4bit,
                    device_map = device_map,
                    full_finetuning = full_finetuning,
                    token = hf_token,
                    trust_remote_code = trust_remote_code,
                )
                logger.info("Loaded text model")

            raise_if_offloaded(self.model, device_map, "Studio training")

            if self.should_stop:
                return False

            if full_finetuning:
                # Enable training mode for full fine-tuning
                # This ensures all model parameters are trainable; otherwise, they might be frozen.
                self.model.for_training()

            self._update_progress(status_message = "Model loaded successfully")
            logger.info("Model loaded successfully")
            return True

        except OSError as e:
            if "could not get source code" in str(e) and not getattr(
                self, "_source_code_retried", False
            ):
                # Unsloth's patching can leave stale state that makes
                # inspect.getsource() fail when switching model families
                # (e.g. gemma3 → gemma3n). The load always succeeds on a
                # second attempt because the failed first call's partial
                # imports clean up the stale state as a side effect.
                self._source_code_retried = True
                logger.info(f"\n'could not get source code' — retrying once...\n")
                return self.load_model(
                    model_name = model_name,
                    max_seq_length = max_seq_length,
                    load_in_4bit = load_in_4bit,
                    hf_token = hf_token,
                    is_dataset_image = is_dataset_image,
                    is_dataset_audio = is_dataset_audio,
                    trust_remote_code = trust_remote_code,
                    full_finetuning = full_finetuning,
                    gpu_ids = gpu_ids,
                )
            error_msg = str(e)
            error_lower = error_msg.lower()
            if any(
                k in error_lower
                for k in (
                    "gated repo",
                    "access to it at",
                    "401",
                    "403",
                    "unauthorized",
                    "forbidden",
                )
            ):
                error_msg = (
                    f"Access denied for '{model_name}'. This model is gated or private. "
                    f"Please add a Hugging Face token with access and try again."
                )
            logger.error(f"Error loading model: {e}")
            self._update_progress(error = error_msg, is_training = False)
            return False
        except Exception as e:
            error_msg = str(e)
            # Catch gated/auth errors and surface a friendly message
            error_lower = error_msg.lower()
            if any(
                k in error_lower
                for k in (
                    "gated repo",
                    "access to it at",
                    "401",
                    "403",
                    "unauthorized",
                    "forbidden",
                )
            ):
                error_msg = (
                    f"Access denied for '{model_name}'. This model is gated or private. "
                    f"Please add a Hugging Face token with access and try again."
                )
            logger.error(f"Error loading model: {e}")
            self._update_progress(error = error_msg, is_training = False)
            return False
        finally:
            self._source_code_retried = False