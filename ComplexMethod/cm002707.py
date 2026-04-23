def align_special_tokens(model, processing_class):
    """
    Aligns the special tokens of the tokenizer with the model configs.

    A new tokens may be defined in the tokenizer for fine-tuning purposes, e.g. an "end of turn" token may be
    added on chat models. In that case, we want the model configs to be aligned with the tokenizer, so that all
    downstream uses work as expected. This alignment should happen before training, to ensure the prediction step
    uses the new tokens as well.
    """
    from .processing_utils import ProcessorMixin
    from .tokenization_utils_base import PreTrainedTokenizerBase

    if isinstance(processing_class, ProcessorMixin):
        tokenizer: PreTrainedTokenizerBase = processing_class.tokenizer
    else:
        tokenizer = processing_class
    model_has_generation_config = hasattr(model, "generation_config") and model.generation_config is not None
    updated_tokens = {}

    # 1 - Align EOS token. EOS is more complex than the others, as `generation_config` may hold more than one EOS
    # token.
    tokenizer_has_new_eos = tokenizer.eos_token_id != getattr(model.config, "eos_token_id", None)
    if model_has_generation_config:
        # `generation_config.eos_token_id` is None: direct comparison
        if model.generation_config.eos_token_id is None:
            tokenizer_has_new_eos |= tokenizer.eos_token_id != model.generation_config.eos_token_id
        else:
            # `generation_config.eos_token_id` is an `int`: convert it to list (and continue below)
            if isinstance(model.generation_config.eos_token_id, int):
                model.generation_config.eos_token_id = [model.generation_config.eos_token_id]
            # `generation_config.eos_token_id` is a `list`: check if the tokenizer's EOS token is in the list
            tokenizer_has_new_eos |= tokenizer.eos_token_id not in model.generation_config.eos_token_id

    if tokenizer_has_new_eos:
        updated_tokens["eos_token_id"] = tokenizer.eos_token_id
        model.config.eos_token_id = tokenizer.eos_token_id
        # The generation config may hold more than one EOS token. We preserve the original EOS tokens: any of the
        # EOS tokens defined here will halt generation.
        if model_has_generation_config:
            all_eos_tokens = [tokenizer.eos_token_id]
            if model.generation_config.eos_token_id is not None:
                all_eos_tokens += list(model.generation_config.eos_token_id)
            model.generation_config.eos_token_id = [token for token in all_eos_tokens if token is not None]

    # 2 - Align BOS
    tokenizer_has_new_bos = tokenizer.bos_token_id != getattr(model.config, "bos_token_id", None)
    if model_has_generation_config:
        tokenizer_has_new_bos |= tokenizer.bos_token_id != model.generation_config.bos_token_id

    if tokenizer_has_new_bos:
        updated_tokens["bos_token_id"] = tokenizer.bos_token_id
        model.config.bos_token_id = tokenizer.bos_token_id
        if model_has_generation_config:
            model.generation_config.bos_token_id = tokenizer.bos_token_id

    # 3 - Align PAD
    tokenizer_has_new_pad = tokenizer.pad_token_id != getattr(model.config, "pad_token_id", None)
    if model_has_generation_config:
        tokenizer_has_new_pad |= tokenizer.pad_token_id != model.generation_config.pad_token_id

    if tokenizer_has_new_pad:
        updated_tokens["pad_token_id"] = tokenizer.pad_token_id
        model.config.pad_token_id = tokenizer.pad_token_id
        if model_has_generation_config:
            model.generation_config.pad_token_id = tokenizer.pad_token_id

    # 4 - Warn users about the changes
    if len(updated_tokens) > 0:
        logger.warning(
            "The tokenizer has new PAD/BOS/EOS tokens that differ from the model config and generation config. "
            "The model config and generation config were aligned accordingly, being updated with the tokenizer's "
            f"values. Updated tokens: {updated_tokens}."
        )