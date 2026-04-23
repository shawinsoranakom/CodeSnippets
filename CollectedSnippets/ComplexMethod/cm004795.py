def convert_dpt_checkpoint(checkpoint_url, pytorch_dump_folder_path, push_to_hub, model_name):
    """
    Copy/paste/tweak model's weights to our DPT structure.
    """

    # define DPT configuration based on URL
    config, expected_shape = get_dpt_config(checkpoint_url)
    # load original state_dict from URL
    state_dict = torch.hub.load_state_dict_from_url(checkpoint_url, map_location="cpu")
    # remove certain keys
    remove_ignore_keys_(state_dict)
    # rename keys
    for key in state_dict.copy():
        val = state_dict.pop(key)
        state_dict[rename_key(key)] = val
    # read in qkv matrices
    read_in_q_k_v(state_dict, config)

    # load HuggingFace model
    model = DPTForSemanticSegmentation(config) if "ade" in checkpoint_url else DPTForDepthEstimation(config)
    model.load_state_dict(state_dict)
    model.eval()

    # Check outputs on an image
    size = 480 if "ade" in checkpoint_url else 384
    image_processor = DPTImageProcessor(size=size)

    image = prepare_img()
    encoding = image_processor(image, return_tensors="pt")

    # forward pass
    outputs = model(**encoding).logits if "ade" in checkpoint_url else model(**encoding).predicted_depth

    # Assert logits
    expected_slice = torch.tensor([[6.3199, 6.3629, 6.4148], [6.3850, 6.3615, 6.4166], [6.3519, 6.3176, 6.3575]])
    if "ade" in checkpoint_url:
        expected_slice = torch.tensor([[4.0480, 4.2420, 4.4360], [4.3124, 4.5693, 4.8261], [4.5768, 4.8965, 5.2163]])
    assert outputs.shape == torch.Size(expected_shape)
    assert (
        torch.allclose(outputs[0, 0, :3, :3], expected_slice, atol=1e-4)
        if "ade" in checkpoint_url
        else torch.allclose(outputs[0, :3, :3], expected_slice)
    )
    print("Looks ok!")

    if pytorch_dump_folder_path is not None:
        Path(pytorch_dump_folder_path).mkdir(exist_ok=True)
        print(f"Saving model to {pytorch_dump_folder_path}")
        model.save_pretrained(pytorch_dump_folder_path)
        print(f"Saving image processor to {pytorch_dump_folder_path}")
        image_processor.save_pretrained(pytorch_dump_folder_path)

    if push_to_hub:
        print("Pushing model to hub...")
        model.push_to_hub(repo_id=f"nielsr/{model_name}")
        image_processor.push_to_hub(repo_id=f"nielsr/{model_name}")