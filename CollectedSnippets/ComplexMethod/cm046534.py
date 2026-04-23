async def list_models(
    current_subject: str = Depends(get_current_subject),
):
    """
    List available models (default models and loaded models).

    This endpoint returns the default models and any currently loaded models.
    """
    try:
        inference_backend = get_inference_backend()

        # Get default models
        default_models = inference_backend.default_models

        # Get loaded models
        loaded_models = []
        for model_name, model_data in inference_backend.models.items():
            _is_vision = model_data.get("is_vision", False)
            _audio_type = model_data.get("audio_type")
            model_info = ModelDetails(
                id = model_name,
                name = model_name.split("/")[-1] if "/" in model_name else model_name,
                is_vision = _is_vision,
                is_lora = model_data.get("is_lora", False),
                is_audio = model_data.get("is_audio", False),
                audio_type = _audio_type,
                has_audio_input = model_data.get("has_audio_input", False),
                model_type = derive_model_type(_is_vision, _audio_type),
            )
            loaded_models.append(model_info)

        # Include active GGUF model (loaded via llama-server)
        from routes.inference import get_llama_cpp_backend

        llama_backend = get_llama_cpp_backend()
        if llama_backend.is_loaded and llama_backend.model_identifier:
            loaded_models.append(
                ModelDetails(
                    id = llama_backend.model_identifier,
                    name = llama_backend.model_identifier.split("/")[-1],
                    is_gguf = True,
                    is_vision = llama_backend.is_vision,
                    is_audio = getattr(llama_backend, "_is_audio", False),
                    audio_type = getattr(llama_backend, "_audio_type", None),
                )
            )

        # Combine default and loaded models
        all_models = []
        seen_ids = set()

        # Add default models
        for model_id in default_models:
            if model_id not in seen_ids:
                model_info = ModelDetails(
                    id = model_id,
                    name = model_id.split("/")[-1] if "/" in model_id else model_id,
                    is_gguf = model_id.upper().endswith("-GGUF"),
                )
                all_models.append(model_info)
                seen_ids.add(model_id)

        # Add loaded models
        for model_info in loaded_models:
            if model_info.id not in seen_ids:
                all_models.append(model_info)
                seen_ids.add(model_info.id)

        return ModelListResponse(models = all_models, default_models = default_models)

    except Exception as e:
        logger.error(f"Error listing models: {e}", exc_info = True)
        raise HTTPException(status_code = 500, detail = f"Failed to list models: {str(e)}")