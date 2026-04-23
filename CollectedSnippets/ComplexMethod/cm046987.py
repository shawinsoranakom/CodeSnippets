def resolve_attention_implementation(
    model_class,
    config,
    requested_attn_implementation = None,
    supports_sdpa = None,
):
    model_type_name = _config_get(config, "model_type", "")
    model_type = model_type_name.lower()
    if supports_sdpa is None:
        supports_sdpa = model_class is not None and getattr(
            model_class, "_supports_sdpa", False
        )
    supports_flash_attention = model_class is not None and (
        getattr(model_class, "_supports_flash_attn_2", False)
        or getattr(model_class, "_supports_flash_attn", False)
    )
    disable_reason = _get_flash_attention_disable_reason(config)
    flash_attention_disabled = disable_reason is not None

    if model_class is None:
        attn_impl = _set_attn_impl(config, "sdpa" if supports_sdpa else "eager")
    else:
        if _is_eager_only(model_type):
            attn_impl = _set_attn_impl(config, "eager")
        elif flash_attention_disabled:
            attn_impl = _disable_flash_attention_if_needed(
                config,
                supports_sdpa = supports_sdpa,
                would_use_flash_attention = (
                    HAS_FLASH_ATTENTION and supports_flash_attention
                ),
                disable_reason = disable_reason,
            )
        elif HAS_FLASH_ATTENTION and supports_flash_attention:
            attn_impl = _set_attn_impl(config, "flash_attention_2")
        elif supports_sdpa:
            attn_impl = _set_attn_impl(config, "sdpa")
        else:
            attn_impl = "eager"
            if os.environ.get("UNSLOTH_ENABLE_FLEX_ATTENTION", "1") != "0":
                try:
                    from transformers.utils.import_utils import (
                        is_torch_flex_attn_available,
                    )

                    if (
                        is_torch_flex_attn_available()
                        and getattr(model_class, "_supports_flex_attn", False)
                        and not _is_flex_excluded(model_type)
                    ):
                        attention_dropout = (
                            _config_get(config, "attention_dropout", 0) or 0
                        )
                        if attention_dropout == 0:
                            attn_impl = _set_attn_impl(config, "flex_attention")
                except Exception:
                    pass
            if attn_impl == "eager":
                attn_impl = _set_attn_impl(config, "eager")

    if requested_attn_implementation is None:
        final_attn_impl = attn_impl
    elif flash_attention_disabled:
        final_attn_impl = _disable_flash_attention_if_needed(
            config,
            requested_attn_implementation,
            supports_sdpa = supports_sdpa,
            disable_reason = disable_reason,
        )
    else:
        final_attn_impl = requested_attn_implementation
        _set_attn_impl(config, final_attn_impl)

    if not supports_sdpa and final_attn_impl == "sdpa":
        print(
            f"Unsloth: {(model_type_name or 'model').title()} does not support SDPA - switching to fast eager."
        )
        final_attn_impl = _set_attn_impl(config, "eager")

    return final_attn_impl