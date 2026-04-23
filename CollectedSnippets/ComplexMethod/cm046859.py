def _fix_chat_template_for_tokenizer(tokenizer, chat_template):
    """Entry point for a string chat_template. Runs the no==yes diagnostic,
    attempts repair if needed, and returns the (possibly patched) template.

    On repair failure, the behavior is controlled by
    UNSLOTH_STRICT_CHAT_TEMPLATE: warn + return original (default) or raise
    RuntimeError (strict)."""
    name = getattr(tokenizer, "name_or_path", "unknown")
    source_path = getattr(tokenizer, "_source_path", name)

    # Detect ShareGPT vs HF style by probing apply_chat_template.
    is_sharegpt = None
    try:
        tokenizer.apply_chat_template(
            [{"role": "user", "content": "Who are you?"}],
            add_generation_prompt = False,
            tokenize = False,
        )
        is_sharegpt = False
    except Exception:
        try:
            tokenizer.apply_chat_template(
                [{"from": "human", "value": "Who are you?"}],
                add_generation_prompt = False,
                tokenize = False,
            )
            is_sharegpt = True
        except Exception:
            is_sharegpt = None

    if is_sharegpt is None:
        return chat_template

    messages = (
        [{"from": "human", "value": "Who are you?"}]
        if is_sharegpt
        else [{"role": "user", "content": "Who are you?"}]
    )
    try:
        no = tokenizer.apply_chat_template(
            messages,
            add_generation_prompt = False,
            tokenize = False,
        )
        yes = tokenizer.apply_chat_template(
            messages,
            add_generation_prompt = True,
            tokenize = False,
        )
    except Exception:
        return chat_template

    if no != yes:
        # Template already responds to the flag; leave as is.
        return chat_template

    # no == yes: template ignores add_generation_prompt. Try to repair.
    if _has_add_generation_prompt_block(chat_template):
        # Template has the block but it does not change output. This is the
        # "wasn't provided correctly" case from the pre-warn code path.
        strict = _is_strict_chat_template_mode()
        msg = _format_chat_template_message(
            name,
            repaired = False,
            has_generation_block = True,
            local_path_source = source_path,
            strict = strict,
        )
        if strict:
            raise RuntimeError(msg)
        logger.warning_once(msg)
        return chat_template

    repaired = _repair_string_template(tokenizer, chat_template, is_sharegpt)
    if repaired is not None:
        logger.warning_once(
            _format_chat_template_message(
                name,
                repaired = True,
                local_path_source = source_path,
            )
        )
        return repaired

    strict = _is_strict_chat_template_mode()
    msg = _format_chat_template_message(
        name,
        repaired = False,
        local_path_source = source_path,
        strict = strict,
    )
    if strict:
        raise RuntimeError(msg)
    logger.warning_once(msg)
    return chat_template