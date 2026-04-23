def convert_mobilevitv2_checkpoint(task_name, checkpoint_path, orig_config_path, pytorch_dump_folder_path):
    """
    Copy/paste/tweak model's weights to our MobileViTV2 structure.
    """
    config = get_mobilevitv2_config(task_name, orig_config_path)

    # load original state_dict
    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=True)

    # load huggingface model
    if task_name.startswith("ade20k_") or task_name.startswith("voc_"):
        model = MobileViTV2ForSemanticSegmentation(config).eval()
        base_model = False
    else:
        model = MobileViTV2ForImageClassification(config).eval()
        base_model = False

    # remove and rename some keys of load the original model
    state_dict = checkpoint
    remove_unused_keys(state_dict)
    rename_keys = create_rename_keys(state_dict, base_model=base_model)
    for rename_key_src, rename_key_dest in rename_keys:
        rename_key(state_dict, rename_key_src, rename_key_dest)

    # load modified state_dict
    model.load_state_dict(state_dict)

    # Check outputs on an image, prepared by MobileViTImageProcessor
    image_processor = MobileViTImageProcessor(crop_size=config.image_size, size=config.image_size + 32)
    encoding = image_processor(images=prepare_img(), return_tensors="pt")
    outputs = model(**encoding)

    # verify classification model
    if task_name.startswith("imagenet"):
        logits = outputs.logits
        predicted_class_idx = logits.argmax(-1).item()
        print("Predicted class:", model.config.id2label[predicted_class_idx])
        if task_name.startswith("imagenet1k_256") and config.width_multiplier == 1.0:
            # expected_logits for base variant
            expected_logits = torch.tensor([-1.6336e00, -7.3204e-02, -5.1883e-01])
            assert torch.allclose(logits[0, :3], expected_logits, atol=1e-4)

    Path(pytorch_dump_folder_path).mkdir(exist_ok=True)
    print(f"Saving model {task_name} to {pytorch_dump_folder_path}")
    model.save_pretrained(pytorch_dump_folder_path)
    print(f"Saving image processor to {pytorch_dump_folder_path}")
    image_processor.save_pretrained(pytorch_dump_folder_path)