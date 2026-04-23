def get_config_overrides(config_class, processors):
    # `Bark` configuration is too special. Let's just not handle this for now.
    if config_class.__name__ == "BarkConfig":
        return {}

    config_overrides = {}

    # Check if there is any tokenizer (prefer fast version if any)
    tokenizer = None
    for processor in processors:
        if isinstance(processor, PreTrainedTokenizerFast):
            tokenizer = processor
            break
        elif isinstance(processor, PythonBackend):
            tokenizer = processor

    if tokenizer is None:
        return config_overrides

    # Get some properties of the (already converted) tokenizer (smaller vocab size, special token ids, etc.)
    # We use `len(tokenizer)` instead of `tokenizer.vocab_size` to avoid potential issues for tokenizers with non-empty
    # `added_tokens_encoder`. One example is the `DebertaV2Tokenizer` where the mask token is the extra token.
    vocab_size = len(tokenizer)

    # The original checkpoint has length `35998`, but it doesn't have ids `30400` and `30514` but instead `35998` and
    # `35999`.
    if config_class.__name__ == "GPTSanJapaneseConfig":
        vocab_size += 2

    config_overrides["vocab_size"] = vocab_size

    # Used to create a new model tester with `tokenizer.vocab_size` in order to get the (updated) special token ids.
    model_tester_kwargs = {"vocab_size": vocab_size}
    # `FSMTModelTester` accepts `src_vocab_size` and `tgt_vocab_size` but not `vocab_size`.
    if config_class.__name__ == "FSMTConfig":
        del model_tester_kwargs["vocab_size"]
        model_tester_kwargs["src_vocab_size"] = tokenizer.src_vocab_size
        model_tester_kwargs["tgt_vocab_size"] = tokenizer.tgt_vocab_size

    _tiny_config = get_tiny_config(config_class, **model_tester_kwargs)

    # handle the possibility of `text_config` inside `_tiny_config` for clip-like models (`owlvit`, `groupvit`, etc.)
    if hasattr(_tiny_config, "text_config"):
        _tiny_config = _tiny_config.text_config

    # Collect values of some special token ids
    for attr in dir(_tiny_config):
        if attr.endswith("_token_id"):
            token_id = getattr(_tiny_config, attr)
            if token_id is not None:
                # Using the token id values from `tokenizer` instead of from `_tiny_config`.
                token_id = get_token_id_from_tokenizer(attr, tokenizer, original_token_id=token_id)
                config_overrides[attr] = token_id

    if config_class.__name__ == "FSMTConfig":
        config_overrides["src_vocab_size"] = tokenizer.src_vocab_size
        config_overrides["tgt_vocab_size"] = tokenizer.tgt_vocab_size

        # TODO: removed by raushan in #41250
        # # `FSMTConfig` has `DecoderConfig` as `decoder` attribute.
        # config_overrides["decoder"] = configuration_fsmt.DecoderConfig(
        #     vocab_size=tokenizer.tgt_vocab_size, bos_token_id=config_overrides["eos_token_id"]
        # )

    # Marian failed to convert the tokenzier, and has `'vocab_size': 58101` and `'pad_token_id': 58100`.
    # which gives `Padding_idx must be within num_embeddings`
    if config_class.__name__ == "MarianConfig":
        config_overrides["decoder_vocab_size"] = config_overrides["vocab_size"]

    return config_overrides