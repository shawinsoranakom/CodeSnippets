def convert_zoedepth_checkpoint(model_name, pytorch_dump_folder_path, push_to_hub):
    """
    Copy/paste/tweak model's weights to our ZoeDepth structure.
    """

    # define ZoeDepth configuration based on URL
    config, _ = get_zoedepth_config(model_name)

    # load original model
    original_model = torch.hub.load(
        "NielsRogge/ZoeDepth:understanding_zoedepth", model_name, pretrained=True, force_reload=True
    )
    original_model.eval()
    state_dict = original_model.state_dict()

    print("Original state dict:")
    for name, param in state_dict.items():
        print(name, param.shape)

    # read in qkv matrices
    read_in_q_k_v(state_dict, config)
    if model_name == "ZoeD_NK":
        read_in_q_k_v_metric_head(state_dict)

    # rename keys
    state_dict = convert_state_dict(state_dict)
    # remove certain keys
    remove_ignore_keys(state_dict)

    # load HuggingFace model
    model = ZoeDepthForDepthEstimation(config)
    model.load_state_dict(state_dict)
    model.eval()

    # verify image processor
    image = prepare_img()

    image_processor = ZoeDepthImageProcessor()
    pixel_values = image_processor(image, return_tensors="pt").pixel_values
    filepath = hf_hub_download(
        repo_id="nielsr/test-image",
        filename="zoedepth_pixel_values.pt",
        repo_type="dataset",
    )
    original_pixel_values = torch.load(filepath, map_location="cpu", weights_only=True)
    assert torch.allclose(pixel_values, original_pixel_values)

    # verify logits
    # this was done on a resized version of the cats image (384x384)
    filepath = hf_hub_download(
        repo_id="nielsr/test-image",
        filename="zoedepth_pixel_values.pt",
        repo_type="dataset",
        revision="1865dbb81984f01c89e83eec10f8d07efd10743d",
    )
    cats_pixel_values = torch.load(filepath, map_location="cpu", weights_only=True)
    depth = model(cats_pixel_values).predicted_depth

    # Verify logits
    # These were obtained by inserting the pixel_values at the patch embeddings of BEiT
    if model_name == "ZoeD_N":
        expected_shape = torch.Size([1, 384, 384])
        expected_slice = torch.tensor([[1.0328, 1.0604, 1.0747], [1.0816, 1.1293, 1.1456], [1.1117, 1.1629, 1.1766]])
    elif model_name == "ZoeD_K":
        expected_shape = torch.Size([1, 384, 384])
        expected_slice = torch.tensor([[1.6567, 1.6852, 1.7065], [1.6707, 1.6764, 1.6713], [1.7195, 1.7166, 1.7118]])
    elif model_name == "ZoeD_NK":
        expected_shape = torch.Size([1, 384, 384])
        expected_slice = torch.tensor([[1.1228, 1.1079, 1.1382], [1.1807, 1.1658, 1.1891], [1.2344, 1.2094, 1.2317]])

    print("Shape of depth:", depth.shape)
    print("First 3x3 slice of depth:", depth[0, :3, :3])

    assert depth.shape == torch.Size(expected_shape)
    assert torch.allclose(depth[0, :3, :3], expected_slice, atol=1e-4)
    print("Looks ok!")

    if pytorch_dump_folder_path is not None:
        print(f"Saving model and processor to {pytorch_dump_folder_path}")
        Path(pytorch_dump_folder_path).mkdir(exist_ok=True)
        model.save_pretrained(pytorch_dump_folder_path)
        image_processor.save_pretrained(pytorch_dump_folder_path)

    if push_to_hub:
        model_name_to_repo_id = {
            "ZoeD_N": "zoedepth-nyu",
            "ZoeD_K": "zoedepth-kitti",
            "ZoeD_NK": "zoedepth-nyu-kitti",
        }

        print("Pushing model and processor to the hub...")
        repo_id = model_name_to_repo_id[model_name]
        model.push_to_hub(f"Intel/{repo_id}")
        image_processor = ZoeDepthImageProcessor()
        image_processor.push_to_hub(f"Intel/{repo_id}")