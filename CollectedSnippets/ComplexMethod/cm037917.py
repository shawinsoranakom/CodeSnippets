def _get_language_model_for_seq_cls(model) -> nn.Module:
    """
    Get the language model component for sequence classification conversion.
    For VLMs, returns the inner language model. For standard LLMs, returns model itself.
    """
    if supports_multimodal(model):
        try:
            lm = model.get_language_model()
            if lm is not model:
                return lm
        except Exception:
            pass

    for attr_name in ("language_model", "lm", "text_model"):
        if hasattr(model, attr_name):
            candidate = getattr(model, attr_name)
            if (
                isinstance(candidate, nn.Module)
                and candidate is not model
                and hasattr(candidate, "model")
            ):
                return candidate

    for name, child in model.named_children():
        child_name = type(child).__name__
        if ("ForCausalLM" in child_name or "LMHead" in child_name) and hasattr(
            child, "model"
        ):
            return child

    return model