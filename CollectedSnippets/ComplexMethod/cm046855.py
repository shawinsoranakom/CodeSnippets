def load_correct_tokenizer(
    tokenizer_name,
    model_max_length = None,
    padding_side = "right",
    token = None,
    trust_remote_code = False,
    cache_dir = "huggingface_tokenizers_cache",
    fix_tokenizer = True,
):
    tokenizer = _load_correct_tokenizer(
        tokenizer_name = tokenizer_name,
        model_max_length = model_max_length,
        padding_side = padding_side,
        token = token,
        trust_remote_code = trust_remote_code,
        cache_dir = cache_dir,
        fix_tokenizer = fix_tokenizer,
    )

    ### 1. Fixup tokenizer's chat_template
    old_chat_template = getattr(tokenizer, "chat_template", None)

    # Ignore mistral type models since they don't have an add_generation_prompt
    if any(
        s in str(getattr(tokenizer, "name_or_path", "")).lower()
        for s in ["mistral", "qwen3guard"]
    ):
        chat_template = old_chat_template

    # Also check Llama-2 old style models
    elif (
        old_chat_template is not None
        and "[/INST]" in old_chat_template
        and "[INST]" in old_chat_template
        and "bos_token" in old_chat_template
        and "eos_token" in old_chat_template
    ):
        chat_template = old_chat_template

    else:
        chat_template = fix_chat_template(tokenizer)
        if old_chat_template is not None and chat_template is None:
            raise RuntimeError(
                "Unsloth: Fixing chat template failed - please file a report immediately!"
            )
        pass

    tokenizer.chat_template = chat_template
    return tokenizer