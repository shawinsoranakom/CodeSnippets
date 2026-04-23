def convert_bit_checkpoint(model_name, pytorch_dump_folder_path, push_to_hub=False):
    """
    Copy/paste/tweak model's weights to our BiT structure.
    """

    # define default BiT configuration
    config = get_config(model_name)

    # load original model from timm
    timm_model = create_model(model_name, pretrained=True)
    timm_model.eval()

    # load state_dict of original model
    state_dict = timm_model.state_dict()
    for key in state_dict.copy():
        val = state_dict.pop(key)
        state_dict[rename_key(key)] = val.squeeze() if "head" in key else val

    # load HuggingFace model
    model = BitForImageClassification(config)
    model.eval()
    model.load_state_dict(state_dict)

    # create image processor
    transform = create_transform(**resolve_data_config({}, model=timm_model))
    timm_transforms = transform.transforms

    pillow_resamplings = {
        "bilinear": PILImageResampling.BILINEAR,
        "bicubic": PILImageResampling.BICUBIC,
        "nearest": PILImageResampling.NEAREST,
    }

    processor = BitImageProcessor(
        do_resize=True,
        size={"shortest_edge": timm_transforms[0].size},
        resample=pillow_resamplings[timm_transforms[0].interpolation.value],
        do_center_crop=True,
        crop_size={"height": timm_transforms[1].size[0], "width": timm_transforms[1].size[1]},
        do_normalize=True,
        image_mean=timm_transforms[-1].mean.tolist(),
        image_std=timm_transforms[-1].std.tolist(),
    )

    image = prepare_img()
    timm_pixel_values = transform(image).unsqueeze(0)
    pixel_values = processor(image, return_tensors="pt").pixel_values

    # verify pixel values
    assert torch.allclose(timm_pixel_values, pixel_values)

    # verify logits
    with torch.no_grad():
        outputs = model(pixel_values)
        logits = outputs.logits

    print("Logits:", logits[0, :3])
    print("Predicted class:", model.config.id2label[logits.argmax(-1).item()])
    timm_logits = timm_model(pixel_values)
    assert timm_logits.shape == outputs.logits.shape
    assert torch.allclose(timm_logits, outputs.logits, atol=1e-3)
    print("Looks ok!")

    if pytorch_dump_folder_path is not None:
        Path(pytorch_dump_folder_path).mkdir(exist_ok=True)
        print(f"Saving model {model_name} and processor to {pytorch_dump_folder_path}")
        model.save_pretrained(pytorch_dump_folder_path)
        processor.save_pretrained(pytorch_dump_folder_path)

    if push_to_hub:
        print(f"Pushing model {model_name} and processor to the hub")
        model.push_to_hub(f"ybelkada/{model_name}")
        processor.push_to_hub(f"ybelkada/{model_name}")