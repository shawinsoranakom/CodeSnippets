def main():
    parser = argparse.ArgumentParser(description="Convert GLM-ASR model weights to Hugging Face format")
    parser.add_argument(
        "--input_path_or_repo",
        type=str,
        default="zai-org/GLM-ASR-Nano-2512",
        help="Path to input model file or Hugging Face repository ID",
    )
    parser.add_argument(
        "--revision",
        type=str,
        default="91967eab799804ab256a3819a085b92378906eb2",
        help="Revision of the input repository",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default=None,
        help="Output directory to save the converted model and processor",
    )
    parser.add_argument(
        "--push_to_hub",
        type=str,
        default=None,
        help="Repository ID to push the model and processor to Hub (if not provided, won't push)",
    )

    args = parser.parse_args()

    path = cached_file(args.input_path_or_repo, "model.safetensors", revision=args.revision)
    state_dict = load_file(path)

    config = GlmAsrConfig()
    model = GlmAsrForConditionalGeneration(config)

    new_state_dict = {}
    for k, v in state_dict.items():
        new_key = convert_key(k, ORIGINAL_TO_CONVERTED_KEY_MAPPING)

        # those are not used
        if new_key in [
            "audio_encoder.audio_bos_eos_token.weight",  # already present in the emb
            "audio_tower.embed_positions.weight",
            "multi_modal_projector.bias",
            "multi_modal_projector.weight",
        ]:
            continue

        if "audio_tower" in new_key and ("q_proj" in new_key or "k_proj" in new_key):
            v = permute_rope(v, config)

        new_state_dict[new_key] = v

    model.load_state_dict(new_state_dict, strict=True, assign=True)

    feature_extractor = WhisperFeatureExtractor(feature_size=128)
    tokenizer = TokenizersBackend.from_pretrained(args.input_path_or_repo, revision=args.revision)
    tokenizer.pad_token = tokenizer.eos_token

    processor = GlmAsrProcessor(feature_extractor=feature_extractor, tokenizer=tokenizer, chat_template=chat_template)

    if args.output_dir:
        model.save_pretrained(args.output_dir)
        processor.save_pretrained(args.output_dir)

    if args.push_to_hub:
        model.push_to_hub(args.push_to_hub)
        processor.push_to_hub(args.push_to_hub)