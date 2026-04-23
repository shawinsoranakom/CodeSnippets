def convert_dpt_checkpoint(checkpoint_url, pytorch_dump_folder_path, push_to_hub, model_name, show_prediction):
    """
    Copy/paste/tweak model's weights to our DPT structure.
    """

    # define DPT configuration based on URL
    config, expected_shape = get_dpt_config(checkpoint_url)
    # load original state_dict from URL
    # state_dict = torch.hub.load_state_dict_from_url(checkpoint_url, map_location="cpu")
    state_dict = torch.load(checkpoint_url, map_location="cpu", weights_only=True)
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

    if show_prediction:
        prediction = (
            torch.nn.functional.interpolate(
                outputs.unsqueeze(1),
                size=(image.size[1], image.size[0]),
                mode="bicubic",
                align_corners=False,
            )
            .squeeze()
            .cpu()
            .numpy()
        )

        Image.fromarray((prediction / prediction.max()) * 255).show()

    if pytorch_dump_folder_path is not None:
        Path(pytorch_dump_folder_path).mkdir(exist_ok=True)
        print(f"Saving model to {pytorch_dump_folder_path}")
        model.save_pretrained(pytorch_dump_folder_path)
        print(f"Saving image processor to {pytorch_dump_folder_path}")
        image_processor.save_pretrained(pytorch_dump_folder_path)

    if push_to_hub:
        model.push_to_hub("ybelkada/dpt-hybrid-midas")
        image_processor.push_to_hub("ybelkada/dpt-hybrid-midas")