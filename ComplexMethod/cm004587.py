def convert_dit_checkpoint(checkpoint_url, pytorch_dump_folder_path, push_to_hub=False):
    """
    Copy/paste/tweak model's weights to our BEiT structure.
    """

    # define default BEiT configuration
    has_lm_head = "rvlcdip" not in checkpoint_url
    config = BeitConfig(use_absolute_position_embeddings=True, use_mask_token=has_lm_head)

    # size of the architecture
    if "large" in checkpoint_url or "dit-l" in checkpoint_url:
        config.hidden_size = 1024
        config.intermediate_size = 4096
        config.num_hidden_layers = 24
        config.num_attention_heads = 16

    # labels
    if "rvlcdip" in checkpoint_url:
        config.num_labels = 16
        repo_id = "huggingface/label-files"
        filename = "rvlcdip-id2label.json"
        id2label = json.load(open(hf_hub_download(repo_id, filename, repo_type="dataset"), "r"))
        id2label = {int(k): v for k, v in id2label.items()}
        config.id2label = id2label
        config.label2id = {v: k for k, v in id2label.items()}

    # load state_dict of original model, remove and rename some keys
    state_dict = torch.hub.load_state_dict_from_url(checkpoint_url, map_location="cpu")["model"]

    rename_keys = create_rename_keys(config, has_lm_head=has_lm_head)
    for src, dest in rename_keys:
        rename_key(state_dict, src, dest)
    read_in_q_k_v(state_dict, config, has_lm_head=has_lm_head)

    # load HuggingFace model
    model = BeitForMaskedImageModeling(config) if has_lm_head else BeitForImageClassification(config)
    model.eval()
    model.load_state_dict(state_dict)

    # Check outputs on an image
    image_processor = BeitImageProcessor(
        size=config.image_size, resample=PILImageResampling.BILINEAR, do_center_crop=False
    )
    image = prepare_img()

    encoding = image_processor(images=image, return_tensors="pt")
    pixel_values = encoding["pixel_values"]

    outputs = model(pixel_values)
    logits = outputs.logits

    # verify logits
    expected_shape = [1, 16] if "rvlcdip" in checkpoint_url else [1, 196, 8192]
    assert logits.shape == torch.Size(expected_shape), "Shape of logits not as expected"

    Path(pytorch_dump_folder_path).mkdir(exist_ok=True)
    print(f"Saving model to {pytorch_dump_folder_path}")
    model.save_pretrained(pytorch_dump_folder_path)
    print(f"Saving image processor to {pytorch_dump_folder_path}")
    image_processor.save_pretrained(pytorch_dump_folder_path)

    if push_to_hub:
        if has_lm_head:
            model_name = "dit-base" if "base" in checkpoint_url else "dit-large"
        else:
            model_name = "dit-base-finetuned-rvlcdip" if "dit-b" in checkpoint_url else "dit-large-finetuned-rvlcdip"
        image_processor.push_to_hub(repo_id=f"nielsr/{model_name}")
        model.push_to_hub(repo_id=f"nielsr/{model_name}")