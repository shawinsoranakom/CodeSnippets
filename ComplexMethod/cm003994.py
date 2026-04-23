def main(*args):
    del args

    output_path = _OUTPUT_PATH.value
    variant = _VARIANT.value

    config = _VARIANTS[variant]
    config.text_config.dtype = getattr(torch, _TEXT_DTYPE.value)
    config.vision_config.dtype = getattr(torch, _VISION_DTYPE.value)
    if (audio_config := config.audio_config) is not None:
        audio_config.dtype = getattr(torch, _AUDIO_DTYPE.value)

    if _INCLUDE_CHAT_TEMPLATE.value:
        # Chat template is included for instruction tuned models, which treat
        # both "<eos>" and "<end_of_turn>" as generation stoppers.
        config.eos_token_id = [1, 106]

    logging.info(
        "Converting Gemma 4 (%s) @ %s (language) and %s (vision)",
        variant,
        _TEXT_DTYPE.value,
        _VISION_DTYPE.value,
    )
    state_tree = convert(_CHECKPOINT_PATH.value, config)
    logging.info("Converted Gemma 4 (%s) state tree from Orbax to Hugging Face.", variant)

    with accelerate.init_empty_weights():
        if _TEXT_ONLY.value:
            config = config.text_config
            model = Gemma4ForCausalLM(config=config)
        else:
            model = Gemma4ForConditionalGeneration(config=config)

    model.load_state_dict(state_tree, assign=True)
    logging.info(
        "Loaded Gemma 4 (%s) in Hugging Face Transformers as a %s instance.",
        variant,
        type(model).__name__,
    )
    model.save_pretrained(output_path, state_dict=state_tree, safe_serialization=True)
    logging.info(
        "Saved Gemma 4 (%s) to SafeTensors in %s using %s",
        variant,
        output_path,
        type(model).__name__,
    )
    del model
    del state_tree

    chat_template = _CHAT_TEMPLATE_LARGE if variant in _LARGE_MODEL_VARIANTS else _CHAT_TEMPLATE
    chat_template_kwargs = {"chat_template": chat_template} if _INCLUDE_CHAT_TEMPLATE.value else {}
    response_schema_kwargs = {"response_schema": _RESPONSE_SCHEMA} if _INCLUDE_RESPONSE_SCHEMA.value else {}

    sentencepiece_extractor = SentencePieceExtractor(_TOKENIZER_PATH.value)
    vocab, _, merges = sentencepiece_extractor.extract()
    tokenizer = GemmaTokenizer(
        vocab=vocab,
        merges=merges,
        add_bos_token=False,
        padding_side="left",
        extra_special_tokens={
            "image_token": "<|image|>",
            "boi_token": "<|image>",
            "eoi_token": "<image|>",
            "audio_token": "<|audio|>",
            "boa_token": "<|audio>",
            "eoa_token": "<audio|>",
            "sot_token": "<|turn>",
            "eot_token": "<turn|>",
            "soc_token": "<|channel>",
            "eoc_token": "<channel|>",
            "think_token": "<|think|>",
            "escape_token": '<|"|>',
            "str_token": "<|tool_response>",
            "etr_token": "<tool_response|>",
            "stc_token": "<|tool_call>",
            "etc_token": "<tool_call|>",
            "std_token": "<|tool>",
            "etd_token": "<tool|>",
        },
        **chat_template_kwargs,
        **response_schema_kwargs,
    )

    # Update config multimodal token IDs from the tokenizer.
    # The Gemma4 SPM (262144 vocab) has native <|image> (255999) and <|audio> (256000)
    # tokens, plus <image|> (258882) and <audio|> (258883) for delimiters.
    # Only <image_soft_token> and <audio_soft_token> are added as new tokens (IDs >= 262144).
    config.image_token_id = tokenizer.image_token_id
    config.boi_token_id = tokenizer.convert_tokens_to_ids(tokenizer.boi_token)
    config.eoi_token_id = tokenizer.convert_tokens_to_ids(tokenizer.eoi_token)
    config.audio_token_id = tokenizer.audio_token_id
    config.boa_token_id = tokenizer.convert_tokens_to_ids(tokenizer.boa_token)
    config.eoa_token_id = tokenizer.convert_tokens_to_ids(tokenizer.eoa_token)
    logging.info(
        "Set multimodal token IDs from tokenizer: image=%d, boi=%d, eoi=%d, audio=%d, boa=%d, eoa=%d",
        config.image_token_id,
        config.boi_token_id,
        config.eoi_token_id,
        config.audio_token_id,
        config.boa_token_id,
        config.eoa_token_id,
    )
    # Re-save the config with correct token IDs
    config.save_pretrained(output_path)

    if _TEXT_ONLY.value:
        tokenizer.save_pretrained(output_path)
        logging.info("Saved GemmaTokenizer for %s to %s", variant, output_path)
    else:
        vision_config = config.vision_config
        feature_extractor = Gemma4AudioFeatureExtractor()
        image_processor = Gemma4ImageProcessor(
            image_seq_length=vision_config.default_output_length,
            do_normalize=False,
            max_soft_tokens=vision_config.default_output_length,
            pooling_kernel_size=3,
        )
        video_processor = Gemma4VideoProcessor()
        processor = Gemma4Processor(
            image_processor=image_processor,
            feature_extractor=feature_extractor,
            video_processor=video_processor,
            tokenizer=tokenizer,
            image_seq_length=vision_config.default_output_length,
            **chat_template_kwargs,
        )
        processor.save_pretrained(output_path)

        logging.info("Saved Gemma4Processor for %s to %s", variant, output_path)
        del feature_extractor, image_processor, processor

    generation_config = GenerationConfig(
        pad_token_id=config.get_text_config().pad_token_id,
        bos_token_id=config.get_text_config().bos_token_id,
        eos_token_id=(
            tokenizer.convert_tokens_to_ids([tokenizer.eos_token, tokenizer.eot_token, tokenizer.str_token])
            if _INCLUDE_CHAT_TEMPLATE.value
            else config.get_text_config().eos_token_id
        ),
        temperature=1.0,
        do_sample=True,
        top_k=64,
        top_p=0.95,
    )
    generation_config.save_pretrained(output_path)