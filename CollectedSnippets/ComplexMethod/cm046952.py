def _unsloth_get_final_logit_softcapping(config):
    """Return final_logit_softcapping for a model config, falling back to the
    nested text sub-config for composite models. Handles both:
      - Gemma-4-style configs where the attribute lives on ``config.text_config``
      - T5Gemma-style composite configs where the text sub-config is only
        reachable via ``config.get_text_config()``
    Returns 0 if unset, matching the previous behaviour.
    """
    softcap = getattr(config, "final_logit_softcapping", None)
    if softcap is None:
        text_cfg = getattr(config, "text_config", None)
        if text_cfg is None:
            get_text_config = getattr(config, "get_text_config", None)
            if callable(get_text_config):
                try:
                    text_cfg = get_text_config()
                except (TypeError, ValueError):
                    text_cfg = None
        if text_cfg is not None and text_cfg is not config:
            softcap = getattr(text_cfg, "final_logit_softcapping", None)
    return 0 if softcap is None else softcap