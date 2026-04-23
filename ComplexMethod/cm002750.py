def convert_hiera_checkpoint(args):
    model_name = args.model_name
    base_model = args.base_model
    pytorch_dump_folder_path = args.pytorch_dump_folder_path
    push_to_hub = args.push_to_hub
    mae_model = args.mae_model

    config = get_hiera_config(model_name, base_model, mae_model)

    # Load original hiera model
    original_model_name = model_name.replace("-", "_")
    original_model_name = f"mae_{original_model_name}" if mae_model else original_model_name

    original_checkpoint_name = "mae_in1k_ft_in1k" if not (base_model or mae_model) else "mae_in1k"

    original_model = torch.hub.load(
        "facebookresearch/hiera",
        model=original_model_name,
        pretrained=True,
        checkpoint=original_checkpoint_name,
    )

    original_model.eval()
    original_state_dict = original_model.state_dict()
    # Don't need to remove head for MAE because original implementation doesn't have it on MAE
    if base_model:
        remove_classification_head_(original_state_dict)

    # # Rename keys
    new_state_dict = original_state_dict.copy()
    rename_keys = create_rename_keys(config, base_model, mae_model)

    for src, dest in rename_keys:
        rename_key(new_state_dict, src, dest)

    # Load HF hiera model
    if base_model:
        model = HieraModel(config)
    elif mae_model:
        model = HieraForPreTraining(config)
    else:
        model = HieraForImageClassification(config)

    model.eval()

    missing_keys, unexpected_keys = model.load_state_dict(new_state_dict, strict=False)
    print("Missing keys:", missing_keys)
    print("Unexpected keys:", unexpected_keys)

    input_image = prepare_img()

    original_image_preprocessor = transforms.Compose(
        [
            transforms.Resize(int((256 / 224) * 224), interpolation=transforms.functional.InterpolationMode.BICUBIC),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(IMAGENET_DEFAULT_MEAN, IMAGENET_DEFAULT_STD),
        ]
    )

    image_processor = BitImageProcessor(
        image_mean=IMAGENET_DEFAULT_MEAN, image_std=IMAGENET_DEFAULT_STD, size={"shortest_edge": 256}
    )
    inputs = image_processor(images=input_image, return_tensors="pt")

    expected_pixel_values = original_image_preprocessor(input_image).unsqueeze(0)

    input_image = prepare_img()

    inputs = image_processor(images=input_image, return_tensors="pt")
    expected_pixel_values = original_image_preprocessor(input_image).unsqueeze(0)
    assert torch.allclose(inputs.pixel_values, expected_pixel_values, atol=1e-4)
    print("Pixel values look good!")
    print(f"{inputs.pixel_values[0, :3, :3, :3]=}")

    # If is MAE we pass a noise to generate a random mask
    mask_spatial_shape = [
        i // s // ms for i, s, ms in zip(config.image_size, config.patch_stride, config.masked_unit_size)
    ]
    num_windows = math.prod(mask_spatial_shape)
    torch.manual_seed(2)
    noise = torch.rand(1, num_windows)
    outputs = model(**inputs) if not mae_model else model(noise=noise, **inputs)
    # original implementation returns logits.softmax(dim=-1)

    if base_model:
        expected_prob, expected_intermediates = original_model(expected_pixel_values, return_intermediates=True)
        expected_last_hidden = expected_intermediates[-1]
        batch_size, _, _, hidden_dim = expected_last_hidden.shape
        expected_last_hidden = expected_last_hidden.reshape(batch_size, -1, hidden_dim)
        assert torch.allclose(outputs.last_hidden_state, expected_last_hidden, atol=1e-3)
        print("Base Model looks good as hidden states match original implementation!")
        print(f"{outputs.last_hidden_state[0, :3, :3]=}")
    elif mae_model:
        # get mask from noise to be able to compare outputs
        mask, _ = model.hiera.embeddings.patch_embeddings.random_masking(expected_pixel_values, noise)
        expected_loss, _, _, _ = original_model(expected_pixel_values, mask=mask.bool())
        assert torch.allclose(outputs.loss, expected_loss, atol=1e-3)
        print("MAE Model looks good as loss matches original implementation!")
    else:
        expected_prob = original_model(expected_pixel_values)
        assert torch.allclose(outputs.logits.softmax(dim=-1), expected_prob, atol=1e-3)
        print("Classifier looks good as probs match original implementation")
        print(f"{outputs.logits[:, :5]=}")

    if pytorch_dump_folder_path is not None:
        print(f"Saving model and processor for {model_name} to {pytorch_dump_folder_path}")
        model.save_pretrained(pytorch_dump_folder_path)
        image_processor.save_pretrained(pytorch_dump_folder_path)

    if push_to_hub:
        hub_name = model_name
        if base_model:
            hub_name = model_name
        elif mae_model:
            hub_name = f"{model_name}-mae"
        else:
            hub_name = f"{model_name}-in1k"
        repo_id = f"EduardoPacheco/{hub_name}"
        print(f"Pushing model and processor for {model_name} to hub at {repo_id}")
        model.push_to_hub(repo_id)
        image_processor.push_to_hub(repo_id)