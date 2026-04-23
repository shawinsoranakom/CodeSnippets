def convert_siglip2_checkpoint(model_name, pytorch_dump_folder_path, verify_logits=True, push_to_hub=False):
    """
    Copy/paste/tweak model's weights to our Siglip2 structure.
    """

    # Define Siglip2 configuration
    config = get_siglip2_config(model_name)

    checkpoint = MODEL_NAME_TO_CHECKPOINT_PATH[model_name]
    if not os.path.exists(checkpoint):
        org, repo_id, *filepath = checkpoint.split("/")
        checkpoint = hf_hub_download(repo_id=f"{org}/{repo_id}", filename="/".join(filepath))

    print(f"Loading checkpoint from {checkpoint}...")
    data = np.load(checkpoint)
    state_dict = flatten_nested_dict(data)
    state_dict = split_encoderblock_layers(state_dict)
    state_dict = merge_qkv_for_head(state_dict, config)

    # Rename and transform weights
    print("Renaming and transforming weights...")

    original_keys = list(state_dict.keys())
    hf_keys = convert_old_keys_to_new_keys(original_keys)

    new_state_dict = {}
    for original_key in original_keys:
        new_key = hf_keys[original_key]
        parameter = state_dict.pop(original_key)

        hidden_size = config.vision_config.hidden_size if "vision" in new_key else config.text_config.hidden_size

        if any(k in new_key for k in ("out_proj", "q_proj", "k_proj", "v_proj", "position_embedding")):
            parameter = parameter.reshape(-1, hidden_size)

        # Transpose every weight except for position_embedding and token_embedding
        if new_key.endswith("weight") and "position_embedding" not in new_key and "token_embedding" not in new_key:
            parameter = parameter.T

        # Reshape every bias
        if new_key.endswith("bias"):
            parameter = parameter.reshape(-1)

        new_state_dict[new_key] = torch.from_numpy(parameter)

    # load HuggingFace model
    print("Loading HuggingFace model...")
    model = Siglip2Model(config).eval()
    model.load_state_dict(new_state_dict)

    # Create processor
    print("Creating processor...")
    # TODO: update with more checkpoints
    tokenizer = get_siglip2_tokenizer()
    image_processor = get_siglip2_image_processor(config.vision_config.patch_size, max_num_patches=256)
    processor = Siglip2Processor(image_processor=image_processor, tokenizer=tokenizer)

    # Verify logits
    if verify_logits:
        print(f"Verifying logits for {model_name}...")
        text, images = prepare_inputs()
        inputs = processor(text=text, images=images, padding="max_length", max_length=64, return_tensors="pt")
        outputs = model(**inputs)
        torch.testing.assert_close(outputs.logits_per_text, EXPECTED_OUTPUTS[model_name], atol=1e-3, rtol=1e-3)

    # Save model
    if pytorch_dump_folder_path is not None:
        dst_dir = os.path.join(pytorch_dump_folder_path, model_name)
        print(f"Saving model {model_name} to {dst_dir}...")
        model.save_pretrained(dst_dir)
        print(f"Saving processor to {dst_dir}...")
        processor.save_pretrained(dst_dir)

    if push_to_hub:
        print(f"Pushing model and processor for {model_name} to the HuggingFace Hub...")
        model.push_to_hub(f"qubvel-hf/{model_name}", private=True)
        processor.push_to_hub(f"qubvel-hf/{model_name}", private=True)