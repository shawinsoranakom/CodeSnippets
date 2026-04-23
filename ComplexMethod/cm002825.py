def convert_siglip_checkpoint(model_name, pytorch_dump_folder_path, verify_logits=True, push_to_hub=False):
    """
    Copy/paste/tweak model's weights to our SigLIP structure.
    """

    # Define default SigLIP configuration
    config = get_siglip_config(model_name)

    # Get checkpoint
    checkpoint = model_name_to_checkpoint[model_name]
    if not os.path.exists(checkpoint):
        org, repo_id, *filepath = checkpoint.split("/")
        checkpoint = hf_hub_download(repo_id=f"{org}/{repo_id}", filename="/".join(filepath))

    # Load original state dict
    data = load(checkpoint)
    state_dict = flatten_nested_dict(data)
    state_dict = split_encoderblock_layers(state_dict)

    # Remove and rename some keys
    rename_keys = create_rename_keys(config)
    for src, dest in rename_keys:
        rename_key(state_dict, src, dest, config)

    # qkv matrices of attention pooling head need special treatment
    read_in_q_k_v_head(state_dict, config)

    # Load HuggingFace model
    model = SiglipModel(config).eval()
    model.load_state_dict(state_dict)

    # Create processor
    image_processor = get_image_processor(model_name)
    tokenizer = get_tokenizer(model_name)
    processor = SiglipProcessor(image_processor=image_processor, tokenizer=tokenizer)

    # Verify forward pass on dummy images and texts
    url = "https://cdn.openai.com/multimodal-neurons/assets/apple/apple-ipod.jpg"
    with httpx.stream("GET", url) as response:
        image_1 = Image.open(BytesIO(response.read())).convert("RGB")
    url = "https://cdn.openai.com/multimodal-neurons/assets/apple/apple-blank.jpg"
    with httpx.stream("GET", url) as response:
        image_2 = Image.open(BytesIO(response.read())).convert("RGB")
    texts = ["an apple", "a picture of an apple"]

    inputs = processor(images=[image_1, image_2], text=texts, padding="max_length", max_length=64, return_tensors="pt")
    with torch.no_grad():
        outputs = model(**inputs)

    if verify_logits:
        image_size = config.vision_config.image_size

        # verify input_ids against original ones
        if image_size == 224:
            filename = "siglip_pixel_values.pt"
        elif image_size == 256:
            filename = "siglip_pixel_values_256.pt"
        elif image_size == 384:
            filename = "siglip_pixel_values_384.pt"
        elif image_size == 512:
            filename = "siglip_pixel_values_512.pt"
        else:
            raise ValueError("Image size not supported")

        filepath = hf_hub_download(repo_id="nielsr/test-image", filename=filename, repo_type="dataset")
        original_pixel_values = torch.load(filepath, weights_only=True)
        filepath = hf_hub_download(repo_id="nielsr/test-image", filename="siglip_input_ids.pt", repo_type="dataset")
        original_input_ids = torch.load(filepath, weights_only=True)

        if "i18n" not in model_name:
            assert inputs.input_ids.tolist() == original_input_ids.tolist()

        print("Mean of original pixel values:", original_pixel_values.mean())
        print("Mean of new pixel values:", inputs.pixel_values.mean())

        # note: we're testing with original pixel values here since we don't have exact pixel values
        with torch.no_grad():
            outputs = model(input_ids=original_input_ids, pixel_values=original_pixel_values)
        print(outputs.logits_per_image[:3, :3])

        probs = torch.sigmoid(outputs.logits_per_image)  # these are the probabilities
        print(f"{probs[0][0]:.1%} that image 0 is '{texts[0]}'")
        print(f"{probs[0][1]:.1%} that image 0 is '{texts[1]}'")

        if model_name == "siglip-base-patch16-224":
            expected_slice = torch.tensor(
                [[-2.9621, -2.1672], [-0.2713, 0.2910]],
            )
        elif model_name == "siglip-base-patch16-256":
            expected_slice = torch.tensor(
                [[-3.1146, -1.9894], [-0.7312, 0.6387]],
            )
        elif model_name == "siglip-base-patch16-384":
            expected_slice = torch.tensor(
                [[-2.8098, -2.1891], [-0.4242, 0.4102]],
            )
        elif model_name == "siglip-base-patch16-512":
            expected_slice = torch.tensor(
                [[-2.7899, -2.2668], [-0.4295, -0.0735]],
            )
        elif model_name == "siglip-large-patch16-256":
            expected_slice = torch.tensor(
                [[-1.5827, -0.5801], [-0.9153, 0.1363]],
            )
        elif model_name == "siglip-large-patch16-384":
            expected_slice = torch.tensor(
                [[-2.1523, -0.2899], [-0.2959, 0.7884]],
            )
        elif model_name == "siglip-so400m-patch14-384":
            expected_slice = torch.tensor([[-1.2441, -0.6649], [-0.7060, 0.7374]])
        elif model_name == "siglip-base-patch16-256-i18n":
            expected_slice = torch.tensor(
                [[-0.9064, 0.1073], [-0.0299, 0.5304]],
            )

        assert torch.allclose(outputs.logits_per_image[:3, :3], expected_slice, atol=1e-4)
        print("Looks ok!")

    if pytorch_dump_folder_path is not None:
        pytorch_dump_folder_path = os.path.join(pytorch_dump_folder_path, model_name)
        os.makedirs(pytorch_dump_folder_path, exist_ok=True)
        print(f"Saving model {model_name} to {pytorch_dump_folder_path}")
        model.save_pretrained(pytorch_dump_folder_path)
        print(f"Saving processor to {pytorch_dump_folder_path}")
        processor.save_pretrained(pytorch_dump_folder_path)

    if push_to_hub:
        model.push_to_hub(f"s0225/{model_name}", private=True)
        processor.push_to_hub(f"s0225/{model_name}", private=True)