def convert_maskformer_checkpoint(
    model_name: str, checkpoint_path: str, pytorch_dump_folder_path: str, push_to_hub: bool = False
):
    """
    Copy/paste/tweak model's weights to our MaskFormer structure.
    """
    config = get_maskformer_config(model_name)

    if not strtobool(os.environ.get("TRUST_REMOTE_CODE", "False")):
        raise ValueError(
            "This part uses `pickle.load` which is insecure and will execute arbitrary code that is potentially "
            "malicious. It's recommended to never unpickle data that could have come from an untrusted source, or "
            "that could have been tampered with. If you already verified the pickle data and decided to use it, "
            "you can set the environment variable `TRUST_REMOTE_CODE` to `True` to allow it."
        )
    # load original state_dict
    with open(checkpoint_path, "rb") as f:
        data = pickle.load(f)
    state_dict = data["model"]

    # for name, param in state_dict.items():
    #     print(name, param.shape)

    # rename keys
    rename_keys = create_rename_keys(config)
    for src, dest in rename_keys:
        rename_key(state_dict, src, dest)
    read_in_swin_q_k_v(state_dict, config.backbone_config)
    read_in_decoder_q_k_v(state_dict, config)

    # update to torch tensors
    for key, value in state_dict.items():
        state_dict[key] = torch.from_numpy(value)

    # load 🤗 model
    model = MaskFormerForInstanceSegmentation(config)
    model.eval()

    for name, param in model.named_parameters():
        print(name, param.shape)

    missing_keys, unexpected_keys = model.load_state_dict(state_dict, strict=False)
    assert missing_keys == [
        "model.pixel_level_module.encoder.model.layernorm.weight",
        "model.pixel_level_module.encoder.model.layernorm.bias",
    ]
    assert len(unexpected_keys) == 0, f"Unexpected keys: {unexpected_keys}"

    # verify results
    image = prepare_img()
    if "vistas" in model_name:
        ignore_index = 65
    elif "cityscapes" in model_name:
        ignore_index = 65535
    else:
        ignore_index = 255
    do_reduce_labels = "ade" in model_name
    image_processor = MaskFormerImageProcessor(ignore_index=ignore_index, do_reduce_labels=do_reduce_labels)

    inputs = image_processor(image, return_tensors="pt")

    outputs = model(**inputs)

    print("Logits:", outputs.class_queries_logits[0, :3, :3])

    if model_name == "maskformer-swin-tiny-ade":
        expected_logits = torch.tensor(
            [[3.6353, -4.4770, -2.6065], [0.5081, -4.2394, -3.5343], [2.1909, -5.0353, -1.9323]]
        )
    assert torch.allclose(outputs.class_queries_logits[0, :3, :3], expected_logits, atol=1e-4)
    print("Looks ok!")

    if pytorch_dump_folder_path is not None:
        print(f"Saving model and image processor to {pytorch_dump_folder_path}")
        Path(pytorch_dump_folder_path).mkdir(exist_ok=True)
        model.save_pretrained(pytorch_dump_folder_path)
        image_processor.save_pretrained(pytorch_dump_folder_path)

    if push_to_hub:
        print("Pushing model and image processor to the hub...")
        model.push_to_hub(f"nielsr/{model_name}")
        image_processor.push_to_hub(f"nielsr/{model_name}")