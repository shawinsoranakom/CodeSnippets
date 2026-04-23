def _resolve_moe_parameter_name(model, default_name: str, alternate_name: str) -> str:
    """
    Resolve the actual parameter path for MoE expert weights.

    Most current Unsloth MoE models expose expert weights under
    ``mlp.experts.*``. Gemma4 stores them directly under ``experts.*``.
    Prefer the path that exists on the loaded module when possible.
    """
    if hasattr(model, "named_parameters"):
        try:
            for name, _ in model.named_parameters():
                if name == default_name or name.endswith("." + default_name):
                    return default_name
                if name == alternate_name or name.endswith("." + alternate_name):
                    return alternate_name
        except Exception:
            pass

    config = getattr(model, "config", model)
    model_types = {getattr(config, "model_type", None)}
    text_config = getattr(config, "text_config", None)
    if text_config is not None:
        model_types.add(getattr(text_config, "model_type", None))

    if any(
        isinstance(model_type, str) and model_type.startswith("gemma4")
        for model_type in model_types
    ):
        return alternate_name

    return default_name