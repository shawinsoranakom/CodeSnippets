async def load_model(
    request: LoadRequest,
    fastapi_request: Request,
    current_subject: str = Depends(get_current_subject),
):
    """
    Load a model for inference.

    The model_path should be a clean identifier from GET /models/list.
    Returns inference configuration parameters (temperature, top_p, top_k, min_p)
    from the model's YAML config, falling back to default.yaml for missing values.

    GGUF models are loaded via llama-server (llama.cpp) instead of Unsloth.
    """
    try:
        # Version switching is handled automatically by the subprocess-based
        # inference backend — no need for ensure_transformers_version() here.

        # ── Already-loaded check: skip reload if the exact model is active ──
        backend = get_inference_backend()
        llama_backend = get_llama_cpp_backend()

        if request.gguf_variant:
            if (
                llama_backend.is_loaded
                and llama_backend.hf_variant
                and llama_backend.hf_variant.lower() == request.gguf_variant.lower()
                and llama_backend.model_identifier
                and llama_backend.model_identifier.lower() == request.model_path.lower()
            ):
                logger.info(
                    f"Model already loaded (GGUF): {request.model_path} variant={request.gguf_variant}, skipping reload"
                )
                inference_config = load_inference_config(llama_backend.model_identifier)
                from utils.models import is_audio_input_type

                _gguf_audio = (
                    llama_backend._audio_type
                    if hasattr(llama_backend, "_audio_type")
                    else None
                )
                _gguf_is_audio = getattr(llama_backend, "_is_audio", False)
                return LoadResponse(
                    status = "already_loaded",
                    model = llama_backend.model_identifier,
                    display_name = llama_backend.model_identifier,
                    is_vision = llama_backend._is_vision,
                    is_lora = False,
                    is_gguf = True,
                    is_audio = _gguf_is_audio,
                    audio_type = _gguf_audio,
                    has_audio_input = is_audio_input_type(_gguf_audio)
                    if _gguf_audio
                    else False,
                    inference = inference_config,
                    requires_trust_remote_code = bool(
                        inference_config.get("trust_remote_code", False)
                    ),
                    context_length = llama_backend.context_length,
                    max_context_length = llama_backend.max_context_length,
                    native_context_length = llama_backend.native_context_length,
                    supports_reasoning = llama_backend.supports_reasoning,
                    reasoning_always_on = llama_backend.reasoning_always_on,
                    chat_template = llama_backend.chat_template,
                    speculative_type = llama_backend.speculative_type,
                )
        else:
            if (
                backend.active_model_name
                and backend.active_model_name.lower() == request.model_path.lower()
            ):
                logger.info(
                    f"Model already loaded (Unsloth): {request.model_path}, skipping reload"
                )
                inference_config = load_inference_config(backend.active_model_name)
                _model_info = backend.models.get(backend.active_model_name, {})
                _chat_template = None
                try:
                    _tpl_info = _model_info.get("chat_template_info", {})
                    _chat_template = _tpl_info.get("template")
                except Exception as e:
                    logger.warning(
                        f"Could not retrieve chat template for {backend.active_model_name}: {e}"
                    )
                return LoadResponse(
                    status = "already_loaded",
                    model = backend.active_model_name,
                    display_name = backend.active_model_name,
                    is_vision = _model_info.get("is_vision", False),
                    is_lora = _model_info.get("is_lora", False),
                    is_gguf = False,
                    is_audio = _model_info.get("is_audio", False),
                    audio_type = _model_info.get("audio_type"),
                    has_audio_input = _model_info.get("has_audio_input", False),
                    inference = inference_config,
                    requires_trust_remote_code = bool(
                        inference_config.get("trust_remote_code", False)
                    ),
                    chat_template = _chat_template,
                )

        # Create config using clean factory method
        # is_lora is auto-detected from adapter_config.json on disk/HF
        config = ModelConfig.from_identifier(
            model_id = request.model_path,
            hf_token = request.hf_token,
            gguf_variant = request.gguf_variant,
        )

        if not config:
            raise HTTPException(
                status_code = 400,
                detail = f"Invalid model identifier: {request.model_path}",
            )

        # Normalize gpu_ids: empty list means auto-selection, same as None
        effective_gpu_ids = request.gpu_ids if request.gpu_ids else None

        # ── GGUF path: load via llama-server ──────────────────────
        if config.is_gguf:
            if effective_gpu_ids is not None:
                raise HTTPException(
                    status_code = 400,
                    detail = "gpu_ids is not supported for GGUF models yet.",
                )

            llama_backend = get_llama_cpp_backend()
            unsloth_backend = get_inference_backend()

            # Unload any active Unsloth model first to free VRAM
            if unsloth_backend.active_model_name:
                logger.info(
                    f"Unloading Unsloth model '{unsloth_backend.active_model_name}' before loading GGUF"
                )
                unsloth_backend.unload_model(unsloth_backend.active_model_name)

            # Route to HF mode or local mode based on config
            # Run in a thread so the event loop stays free for progress
            # polling and other requests during the (potentially long)
            # GGUF download + llama-server startup.
            _n_parallel = getattr(fastapi_request.app.state, "llama_parallel_slots", 1)

            if config.gguf_hf_repo:
                # HF mode: download via huggingface_hub then start llama-server
                success = await asyncio.to_thread(
                    llama_backend.load_model,
                    hf_repo = config.gguf_hf_repo,
                    hf_variant = config.gguf_variant,
                    hf_token = request.hf_token,
                    model_identifier = config.identifier,
                    is_vision = config.is_vision,
                    n_ctx = request.max_seq_length,
                    chat_template_override = request.chat_template_override,
                    cache_type_kv = request.cache_type_kv,
                    speculative_type = request.speculative_type,
                    n_parallel = _n_parallel,
                )
            else:
                # Local mode: llama-server loads via -m <path>
                success = await asyncio.to_thread(
                    llama_backend.load_model,
                    gguf_path = config.gguf_file,
                    mmproj_path = config.gguf_mmproj_file,
                    model_identifier = config.identifier,
                    is_vision = config.is_vision,
                    n_ctx = request.max_seq_length,
                    chat_template_override = request.chat_template_override,
                    cache_type_kv = request.cache_type_kv,
                    speculative_type = request.speculative_type,
                    n_parallel = _n_parallel,
                )

            if not success:
                raise HTTPException(
                    status_code = 500,
                    detail = f"Failed to load GGUF model: {config.display_name}",
                )

            logger.info(f"Loaded GGUF model via llama-server: {config.identifier}")

            # Detect TTS audio by probing the loaded model's vocabulary
            from utils.models import is_audio_input_type

            _gguf_audio = llama_backend.detect_audio_type()
            _gguf_is_audio = _gguf_audio in ("snac", "bicodec", "dac")
            llama_backend._is_audio = _gguf_is_audio
            llama_backend._audio_type = _gguf_audio
            if _gguf_is_audio:
                logger.info(f"GGUF model detected as audio: audio_type={_gguf_audio}")
                await asyncio.to_thread(llama_backend.init_audio_codec, _gguf_audio)

            inference_config = load_inference_config(config.identifier)

            return LoadResponse(
                status = "loaded",
                model = config.identifier,
                display_name = config.display_name,
                is_vision = config.is_vision,
                is_lora = False,
                is_gguf = True,
                is_audio = _gguf_is_audio,
                audio_type = _gguf_audio,
                has_audio_input = is_audio_input_type(_gguf_audio),
                inference = inference_config,
                requires_trust_remote_code = bool(
                    inference_config.get("trust_remote_code", False)
                ),
                context_length = llama_backend.context_length,
                max_context_length = llama_backend.max_context_length,
                native_context_length = llama_backend.native_context_length,
                supports_reasoning = llama_backend.supports_reasoning,
                reasoning_always_on = llama_backend.reasoning_always_on,
                supports_tools = llama_backend.supports_tools,
                cache_type_kv = llama_backend.cache_type_kv,
                chat_template = llama_backend.chat_template,
                speculative_type = llama_backend.speculative_type,
            )

        # ── Standard path: load via Unsloth/transformers ──────────
        backend = get_inference_backend()

        # Unload any active GGUF model first
        llama_backend = get_llama_cpp_backend()
        if llama_backend.is_loaded:
            logger.info("Unloading GGUF model before loading Unsloth model")
            llama_backend.unload_model()

        # Shut down any export subprocess to free VRAM
        try:
            from core.export import get_export_backend

            exp_backend = get_export_backend()
            if exp_backend.current_checkpoint:
                logger.info(
                    "Shutting down export subprocess to free GPU memory for inference"
                )
                exp_backend._shutdown_subprocess()
                exp_backend.current_checkpoint = None
                exp_backend.is_vision = False
                exp_backend.is_peft = False
        except Exception as e:
            logger.warning("Could not shut down export subprocess: %s", e)

        # Auto-detect quantization for LoRA adapters from adapter_config.json
        # The training pipeline patches this file with "unsloth_training_method"
        # which is 'qlora' or 'lora'. Only LoRA (16-bit) needs load_in_4bit=False.
        load_in_4bit = request.load_in_4bit
        if config.is_lora and config.path:
            import json
            from pathlib import Path

            adapter_cfg_path = Path(config.path) / "adapter_config.json"
            if adapter_cfg_path.exists():
                try:
                    with open(adapter_cfg_path) as f:
                        adapter_cfg = json.load(f)
                    training_method = adapter_cfg.get("unsloth_training_method")
                    if training_method == "lora" and load_in_4bit:
                        logger.info(
                            f"adapter_config.json says unsloth_training_method='lora' — "
                            f"setting load_in_4bit=False to match 16-bit training"
                        )
                        load_in_4bit = False
                    elif training_method == "qlora" and not load_in_4bit:
                        logger.info(
                            f"adapter_config.json says unsloth_training_method='qlora' — "
                            f"setting load_in_4bit=True to match QLoRA training"
                        )
                        load_in_4bit = True
                    elif training_method:
                        logger.info(
                            f"Training method: {training_method}, load_in_4bit={load_in_4bit}"
                        )
                    else:
                        # No unsloth_training_method — fallback to base model name
                        if (
                            config.base_model
                            and "-bnb-4bit" not in config.base_model.lower()
                            and load_in_4bit
                        ):
                            logger.info(
                                f"No unsloth_training_method in adapter_config.json. "
                                f"Base model '{config.base_model}' has no -bnb-4bit suffix — "
                                f"setting load_in_4bit=False"
                            )
                            load_in_4bit = False
                except Exception as e:
                    logger.warning(f"Could not read adapter_config.json: {e}")

        # Load the model in a thread so the event loop stays free
        # for download progress polling and other requests.
        success = await asyncio.to_thread(
            backend.load_model,
            config = config,
            max_seq_length = request.max_seq_length,
            load_in_4bit = load_in_4bit,
            hf_token = request.hf_token,
            trust_remote_code = request.trust_remote_code,
            gpu_ids = effective_gpu_ids,
        )

        if not success:
            # Check if YAML says this model needs trust_remote_code
            if not request.trust_remote_code:
                model_defaults = load_model_defaults(config.identifier)
                yaml_trust = model_defaults.get("inference", {}).get(
                    "trust_remote_code", False
                )
                if yaml_trust:
                    raise HTTPException(
                        status_code = 400,
                        detail = (
                            f"Model '{config.display_name}' requires trust_remote_code to be enabled. "
                            f"Please enable 'Trust remote code' in Chat Settings and try again."
                        ),
                    )
            raise HTTPException(
                status_code = 500, detail = f"Failed to load model: {config.display_name}"
            )

        logger.info(f"Loaded model: {config.identifier}")

        # Load inference configuration parameters
        inference_config = load_inference_config(config.identifier)

        # Get chat template from tokenizer
        _chat_template = None
        try:
            _model_info = backend.models.get(config.identifier, {})
            _tpl_info = _model_info.get("chat_template_info", {})
            _chat_template = _tpl_info.get("template")
        except Exception:
            pass

        return LoadResponse(
            status = "loaded",
            model = config.identifier,
            display_name = config.display_name,
            is_vision = config.is_vision,
            is_lora = config.is_lora,
            is_gguf = False,
            is_audio = config.is_audio,
            audio_type = config.audio_type,
            has_audio_input = config.has_audio_input,
            inference = inference_config,
            requires_trust_remote_code = bool(
                inference_config.get("trust_remote_code", False)
            ),
            chat_template = _chat_template,
        )

    except HTTPException:
        raise
    except ValueError as e:
        logger.warning("Rejected inference GPU selection: %s", e)
        raise HTTPException(status_code = 400, detail = str(e))
    except Exception as e:
        logger.error(f"Error loading model: {e}", exc_info = True)
        msg = str(e)
        # Surface a friendlier message for models that Unsloth cannot load
        not_supported_hints = [
            "No config file found",
            "not yet supported",
            "is not supported",
            "does not support",
        ]
        if any(h.lower() in msg.lower() for h in not_supported_hints):
            msg = f"This model is not supported yet. Try a different model. (Original error: {msg})"
        raise HTTPException(status_code = 500, detail = f"Failed to load model: {msg}")