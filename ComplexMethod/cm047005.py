def search_models(
    org: str = None,
    base_name: str = None,
    version: str = None,
    size: str = None,
    quant_types: list[QuantType] = None,
    search_pattern: str = None,
) -> list[ModelInfo]:
    """
    Get model info from the registry.

    See registry.ModelInfo for more fields.

    If search_pattern is provided, the full model path will be matched against the pattern, where the model path is the model_id on huggingface hub.

    """
    if not _ARE_MODELS_REGISTERED:
        register_models()

    model_infos = MODEL_REGISTRY.values()
    if org:
        model_infos = [
            model_info for model_info in model_infos if model_info.org == org
        ]
    if base_name:
        model_infos = [
            model_info
            for model_info in model_infos
            if model_info.base_name == base_name
        ]
    if version:
        model_infos = [
            model_info for model_info in model_infos if model_info.version == version
        ]
    if size:
        model_infos = [
            model_info for model_info in model_infos if model_info.size == size
        ]
    if quant_types:
        model_infos = [
            model_info
            for model_info in model_infos
            if any(model_info.quant_type == quant_type for quant_type in quant_types)
        ]
    if search_pattern:
        model_infos = [
            model_info
            for model_info in model_infos
            if search_pattern in model_info.model_path
        ]

    return model_infos