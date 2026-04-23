def load_assistant_model(
    model: PreTrainedModel,
    assistant_model: str | PreTrainedModel | None,
    assistant_tokenizer: PreTrainedTokenizer | None,
) -> tuple[PreTrainedModel | None, PreTrainedTokenizer | None]:
    """
    Prepares the assistant model and the assistant tokenizer for a pipeline whose model that can call `generate`.

    Args:
        model ([`PreTrainedModel`]):
            The main model that will be used by the pipeline to make predictions.
        assistant_model (`str` or [`PreTrainedModel`], *optional*):
            The assistant model that will be used by the pipeline to make predictions.
        assistant_tokenizer ([`PreTrainedTokenizer`], *optional*):
            The assistant tokenizer that will be used by the pipeline to encode data for the model.

    Returns:
        Tuple: The loaded assistant model and (optionally) the loaded tokenizer.
    """
    if not model.can_generate() or assistant_model is None:
        return None, None

    # If the model is passed as a string, load the model and the corresponding tokenizer
    if isinstance(assistant_model, str):
        assistant_config = AutoConfig.from_pretrained(assistant_model)
        loaded_assistant_model = load_model(assistant_model, config=assistant_config)
        loaded_assistant_model = loaded_assistant_model.to(device=model.device, dtype=model.dtype)
        loaded_assistant_tokenizer = AutoTokenizer.from_pretrained(assistant_model)
    else:
        loaded_assistant_model = assistant_model
        loaded_assistant_tokenizer = assistant_tokenizer

    # Finally, let's check the tokenizers: if the two models have different tokenizers, we need to keep the assistant
    # tokenizer
    same_vocab_size = model.config.vocab_size == loaded_assistant_model.config.vocab_size
    same_special_tokens = all(
        getattr(model.config, token) == getattr(loaded_assistant_model.config, token)
        for token in ("eos_token_id", "pad_token_id", "bos_token_id")
    )
    if same_vocab_size and same_special_tokens:
        loaded_assistant_tokenizer = None
    elif loaded_assistant_tokenizer is None:
        raise ValueError(
            "The assistant model has a different tokenizer than the main model. You should pass the assistant "
            "tokenizer."
        )

    return loaded_assistant_model, loaded_assistant_tokenizer