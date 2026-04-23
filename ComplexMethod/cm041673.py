def resize_embedding_layer(
    model: "PreTrainedModel",
    tokenizer: "PreTrainedTokenizer",
    new_special_tokens_config: Optional[dict] = None,
    init_special_tokens: str = "noise_init",
) -> None:
    r"""Resize token embeddings and initialize new tokens.

    Args:
        model: The model to resize
        tokenizer: The tokenizer (used to get target vocab size)
        new_special_tokens_config: Optional dict with token descriptions for semantic initialization
        init_special_tokens: Initialization method ('noise_init', 'desc_init', 'desc_init_w_noise')
    """
    if is_deepspeed_zero3_enabled():
        import deepspeed  # type: ignore

        params = [model.get_input_embeddings().weight]
        if model.get_output_embeddings() is not None and not model.config.tie_word_embeddings:
            params.append(model.get_output_embeddings().weight)

        context_maybe_zero3 = deepspeed.zero.GatheredParameters(params, modifier_rank=0)
    else:
        context_maybe_zero3 = nullcontext()

    with context_maybe_zero3:
        current_embedding_size = model.get_input_embeddings().weight.size(0)

    if len(tokenizer) > current_embedding_size:
        if getattr(model, "quantization_method", None):
            raise ValueError("Cannot resize embedding layers of a quantized model.")

        if not isinstance(model.get_output_embeddings(), torch.nn.Linear):
            raise ValueError("Current model does not support resizing embedding layers.")

        model.resize_token_embeddings(len(tokenizer), pad_to_multiple_of=64)
        with context_maybe_zero3:
            new_embedding_size = model.get_input_embeddings().weight.size(0)
            num_new_tokens = new_embedding_size - current_embedding_size
            logger.info_rank0(
                f"Resizing embeddings: {current_embedding_size} -> {new_embedding_size} (+{num_new_tokens} tokens)"
            )

            # Initialize input embeddings
            _initialize_embeddings(
                model.get_input_embeddings().weight.data,
                num_new_tokens,
                init_special_tokens,
                new_special_tokens_config,
                tokenizer,
                model,
            )

            # Initialize output embeddings if not tied
            if model.get_output_embeddings() is not None and not model.config.tie_word_embeddings:
                _initialize_embeddings(
                    model.get_output_embeddings().weight.data,
                    num_new_tokens,
                    init_special_tokens,
                    new_special_tokens_config,
                    tokenizer,
                    model,
                )

        model.config.vocab_size = new_embedding_size
        logger.info_rank0(f"Resized token embeddings from {current_embedding_size} to {new_embedding_size}.")