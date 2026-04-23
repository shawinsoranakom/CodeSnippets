def _disable_seq_cls_loading_on_inner_model(language_model, is_vlm: bool):
    """
    Context manager to temporarily disable sequence classification loading
    on inner VLM models to prevent recursive seq_cls_model_loader calls.
    """
    if not is_vlm:
        yield
        return

    inner_hf_config = getattr(language_model, "config", None)
    if inner_hf_config is None:
        yield
        return

    inner_text_config = inner_hf_config.get_text_config()
    original_method = getattr(inner_text_config, "method", None)
    original_tokens = getattr(inner_text_config, "classifier_from_token", None)
    original_hf_tokens = getattr(inner_hf_config, "classifier_from_token", None)

    try:
        if original_method is not None:
            inner_text_config.method = None
        if original_tokens is not None:
            inner_text_config.classifier_from_token = None
        if original_hf_tokens is not None:
            inner_hf_config.classifier_from_token = None
        yield
    finally:
        if original_method is not None:
            inner_text_config.method = original_method
        if original_tokens is not None:
            inner_text_config.classifier_from_token = original_tokens
        if original_hf_tokens is not None:
            inner_hf_config.classifier_from_token = original_hf_tokens