def convert_checkpoint(checkpoint_path, output_dir, push_to_hub, bfloat16, max_shard_size):
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    logger.info("Creating processor")
    processor = create_processor(checkpoint_path, output_path)

    logger.info(f"Loading checkpoint from {checkpoint_path}")
    original_state_dict = load_original_checkpoint(checkpoint_path)

    logger.info("Number of parameters in original state dict: " + str(len(original_state_dict)))
    num_acoustic_decoder_params = sum(
        1 for k in original_state_dict.keys() if k.startswith("model.acoustic_tokenizer.decoder.")
    )

    # remove acoustic tokenizer decoder parameters
    logger.info(f"Number of (unused) acoustic tokenizer decoder parameters: {num_acoustic_decoder_params}")
    original_state_dict = {
        k: v for k, v in original_state_dict.items() if not k.startswith("model.acoustic_tokenizer.decoder.")
    }

    logger.info("Converting state dict")
    converted_state_dict = convert_state_dict(original_state_dict)

    logger.info("Creating config")
    config = create_config_from_checkpoint(checkpoint_path)
    config.save_pretrained(str(output_path))

    if bfloat16:
        dtype = torch.bfloat16
    else:
        dtype = torch.float32
    logger.info(f"Creating model with dtype {dtype}")
    model = VibeVoiceAsrForConditionalGeneration(config).to(dtype)
    logger.info("Number of parameters in model state dict: " + str(len(model.state_dict())))

    logger.info("Loading weights into model")
    load_result = model.load_state_dict(converted_state_dict, strict=False)
    if load_result.missing_keys:
        raise ValueError(f"{len(load_result.missing_keys)} missing keys: {load_result.missing_keys}")
    if load_result.unexpected_keys:
        raise ValueError(f"{len(load_result.unexpected_keys)} unexpected keys: {load_result.unexpected_keys}")

    model.generation_config.pad_token_id = processor.tokenizer.convert_tokens_to_ids("<|image_pad|>")
    model.generation_config.eos_token_id = processor.tokenizer.eos_token_id
    model.generation_config.bos_token_id = processor.tokenizer.bos_token_id
    model.generation_config.do_sample = False
    model.generation_config.max_new_tokens = 32768
    model.generation_config.max_length = 32768

    logger.info(f"Saving model to {output_path}")
    model.save_pretrained(str(output_path), max_shard_size=max_shard_size)

    if push_to_hub:
        logger.info(f"Pushing to Hub: {push_to_hub}")
        model.push_to_hub(push_to_hub, max_shard_size=max_shard_size)
        processor.push_to_hub(push_to_hub)

    logger.info("Verifying conversion by reloading model")
    gc.collect()
    VibeVoiceAsrProcessor.from_pretrained(str(output_path))
    VibeVoiceAsrForConditionalGeneration.from_pretrained(str(output_path))
    logger.info("Model reloaded successfully!")
    logger.info("Conversion complete!")