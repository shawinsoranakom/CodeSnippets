def _model_data_to_profile(model_data: dict[str, Any]) -> dict[str, Any]:
    """Convert raw models.dev data into the canonical profile structure."""
    limit = model_data.get("limit") or {}
    modalities = model_data.get("modalities") or {}
    input_modalities = modalities.get("input") or []
    output_modalities = modalities.get("output") or []

    profile = {
        "name": model_data.get("name"),
        "status": model_data.get("status"),
        "release_date": model_data.get("release_date"),
        "last_updated": model_data.get("last_updated"),
        "open_weights": model_data.get("open_weights"),
        "max_input_tokens": limit.get("context"),
        "max_output_tokens": limit.get("output"),
        "text_inputs": "text" in input_modalities,
        "image_inputs": "image" in input_modalities,
        "audio_inputs": "audio" in input_modalities,
        "pdf_inputs": "pdf" in input_modalities or model_data.get("pdf_inputs"),
        "video_inputs": "video" in input_modalities,
        "text_outputs": "text" in output_modalities,
        "image_outputs": "image" in output_modalities,
        "audio_outputs": "audio" in output_modalities,
        "video_outputs": "video" in output_modalities,
        "reasoning_output": model_data.get("reasoning"),
        "tool_calling": model_data.get("tool_call"),
        "tool_choice": model_data.get("tool_choice"),
        "structured_output": model_data.get("structured_output"),
        "attachment": model_data.get("attachment"),
        "temperature": model_data.get("temperature"),
        "image_url_inputs": model_data.get("image_url_inputs"),
        "image_tool_message": model_data.get("image_tool_message"),
        "pdf_tool_message": model_data.get("pdf_tool_message"),
    }

    return {k: v for k, v in profile.items() if v is not None}