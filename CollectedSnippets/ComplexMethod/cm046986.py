def _disable_flash_attention_if_needed(
    config,
    attn_implementation = None,
    supports_sdpa = False,
    would_use_flash_attention = False,
    disable_reason = None,
):
    if disable_reason is None:
        disable_reason = _get_flash_attention_disable_reason(config)
    if disable_reason is None:
        return attn_implementation

    requested_attn_implementation = attn_implementation
    if requested_attn_implementation is None:
        requested_attn_implementation = _config_get(
            config, "_attn_implementation", None
        )
    if requested_attn_implementation is None:
        requested_attn_implementation = _config_get(config, "attn_implementation", None)

    if requested_attn_implementation == "eager":
        return _set_attn_impl(config, "eager")

    fallback_attn_implementation = "sdpa" if supports_sdpa else "eager"
    if (
        _is_flash_attention_requested(requested_attn_implementation)
        or would_use_flash_attention
    ):
        logged_attn_implementation = (
            requested_attn_implementation
            if _is_flash_attention_requested(requested_attn_implementation)
            else "flash_attention_2"
        )
        model_type = _config_get(config, "model_type", "")
        warning_key = (
            model_type,
            logged_attn_implementation,
            fallback_attn_implementation,
            disable_reason,
        )
        if warning_key not in _FLASH_ATTENTION_DISABLED_WARNED:
            _FLASH_ATTENTION_DISABLED_WARNED.add(warning_key)
            print(
                f"Unsloth: `{logged_attn_implementation}` is not supported "
                f"for `{model_type}` because {disable_reason} - "
                f"defaulting to `{fallback_attn_implementation}`."
            )

    return _set_attn_impl(config, fallback_attn_implementation)