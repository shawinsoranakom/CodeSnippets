async def get_model_config(
    model_name: str,
    hf_token: Optional[str] = Query(None),
    current_subject: str = Depends(get_current_subject),
):
    """
    Get configuration for a specific model.

    This endpoint wraps the backend load_model_defaults function.
    """
    try:
        if not is_local_path(model_name):
            resolved = resolve_cached_repo_id_case(model_name)
            if resolved != model_name:
                logger.info(
                    "Using cached repo_id casing '%s' for requested '%s'",
                    resolved,
                    model_name,
                )
            model_name = resolved

        logger.info(f"Getting model config for: {model_name}")
        from utils.models.model_config import detect_audio_type

        # Load model defaults from backend
        config_dict = load_model_defaults(model_name)

        # Detect model capabilities (pass HF token for gated models)
        is_vision = is_vision_model(model_name, hf_token = hf_token)
        is_embedding = is_embedding_model(model_name, hf_token = hf_token)
        audio_type = detect_audio_type(model_name, hf_token = hf_token)

        # Check if it's a LoRA adapter
        is_lora = False
        base_model = None
        max_position_embeddings = None
        try:
            model_config = ModelConfig.from_identifier(model_name)
            is_lora = model_config.is_lora
            base_model = model_config.base_model if is_lora else None
            max_position_embeddings = _get_max_position_embeddings(model_config)
        except Exception:
            pass

        # Fallback: try AutoConfig directly if not found yet
        if max_position_embeddings is None:
            try:
                from transformers import AutoConfig as _AutoConfig

                _trust = model_name.lower().startswith("unsloth/")
                _ac = _AutoConfig.from_pretrained(
                    model_name, trust_remote_code = _trust, token = hf_token
                )
                max_position_embeddings = _get_max_position_embeddings(_ac)
            except Exception:
                pass

        logger.info(
            f"Model config result for {model_name}: is_vision={is_vision}, is_embedding={is_embedding}, audio_type={audio_type}, is_lora={is_lora}, max_position_embeddings={max_position_embeddings}"
        )
        return ModelDetails(
            id = model_name,
            model_name = model_name,
            config = config_dict,
            is_vision = is_vision,
            is_embedding = is_embedding,
            is_lora = is_lora,
            is_audio = audio_type is not None,
            audio_type = audio_type,
            has_audio_input = is_audio_input_type(audio_type),
            model_type = derive_model_type(is_vision, audio_type, is_embedding),
            base_model = base_model,
            max_position_embeddings = max_position_embeddings,
            model_size_bytes = _get_model_size_bytes(model_name, hf_token),
        )

    except Exception as e:
        logger.error(f"Error getting model config: {e}", exc_info = True)
        raise HTTPException(
            status_code = 500, detail = f"Failed to get model config: {str(e)}"
        )