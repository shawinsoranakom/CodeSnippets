def update_input_types(build_config: dotdict) -> dotdict:
    """Update input types for all fields in build_config.

    For model type fields, sets input_types based on model_type:
    - "embedding" -> ["Embeddings"]
    - "language" (default) -> ["LanguageModel"]
    """
    for key, value in build_config.items():
        if isinstance(value, dict):
            # For model type fields, set input_types based on model_type
            if value.get("type") == "model":
                if not value.get("input_types"):
                    model_type = value.get("model_type", "language")
                    value["input_types"] = ["Embeddings"] if model_type == "embedding" else ["LanguageModel"]
            elif value.get("input_types") is None:
                build_config[key]["input_types"] = []
        elif hasattr(value, "input_types") and value.input_types is None:
            value.input_types = []
    return build_config