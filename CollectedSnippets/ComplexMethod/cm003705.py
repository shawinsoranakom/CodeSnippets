def convert_mlcd_checkpoint(model_name, input_dir, output_dir, verify_hidden_state=True, push_to_hub=False):
    """
    Copy/paste/tweak model's weights to our MLCD structure.
    """

    # Define MLCD configuration
    config = get_mlcd_config(model_name)

    checkpoint = MODEL_NAME_TO_CHECKPOINT_PATH[model_name]
    checkpoint_path = os.path.join(input_dir, checkpoint)
    assert os.path.exists(checkpoint_path), f"Checkpoint path ({checkpoint_path}) not found."

    # Load original checkpoint
    print(f"Loading checkpoint from {checkpoint_path}...")
    state_dict = torch.load(checkpoint_path, "cpu")

    # Flatten nested dictionary
    print("Flattening nested dictionary...")
    state_dict = {k.replace("_orig_mod.", ""): v for k, v in state_dict.items()}
    if "positional_embedding" in state_dict:
        state_dict.pop("positional_embedding")
    state_dict = flatten_nested_dict(state_dict)
    state_dict = split_resblocks_layers(state_dict)
    state_dict = chunk_qkv_for_attn(state_dict)

    # Rename and transform weights
    print("Renaming and transforming weights...")
    original_keys = list(state_dict.keys())
    hf_keys = convert_old_keys_to_new_keys(original_keys)
    new_state_dict = {}
    for original_key in original_keys:
        new_key = hf_keys[original_key]
        parameter = state_dict.pop(original_key)
        new_state_dict[new_key] = torch.from_numpy(parameter)

    # load HuggingFace model
    print("Loading HuggingFace model...")
    model = MLCDVisionModel(config).eval()
    model.load_state_dict(new_state_dict)

    # Create processor
    print("Creating processor...")
    image_processor = get_mlcd_image_processor(model_name)

    # Verify hidden state
    if verify_hidden_state:
        print("Verifying hidden state for {model_name}...")
        url = "http://images.cocodataset.org/val2017/000000039769.jpg"
        with httpx.stream("GET", url) as response:
            image = Image.open(BytesIO(response.read()))
        pixel_values = image_processor(image, return_tensors="pt")["pixel_values"]
        last_hidden_state = model(pixel_values, output_hidden_states=True).last_hidden_state[0, :5, :5]
        expected_hidden_state = EXPECTED_OUTPUTS[model_name]
        np.testing.assert_allclose(last_hidden_state.cpu().numpy(), expected_hidden_state.numpy(), atol=1e-4)

    # Save model
    if output_dir is not None:
        dst_dir = os.path.join(output_dir, model_name)
        print(f"Saving model {model_name} to {dst_dir}...")
        model.save_pretrained(dst_dir)
        print(f"Saving processor to {dst_dir}...")
        image_processor.save_pretrained(dst_dir)

    if push_to_hub:
        print(f"Pushing model and processor for {model_name} to the HuggingFace Hub...")
        model.push_to_hub(f"deepglint-hf/{model_name}", private=True)
        image_processor.push_to_hub(f"deepglint-hf/{model_name}", private=True)