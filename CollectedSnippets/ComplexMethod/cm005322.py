def convert_upernet_checkpoint(model_name, pytorch_dump_folder_path, push_to_hub):
    model_name_to_url = {
        "upernet-swin-tiny": "https://download.openmmlab.com/mmsegmentation/v0.5/swin/upernet_swin_tiny_patch4_window7_512x512_160k_ade20k_pretrain_224x224_1K/upernet_swin_tiny_patch4_window7_512x512_160k_ade20k_pretrain_224x224_1K_20210531_112542-e380ad3e.pth",
        "upernet-swin-small": "https://download.openmmlab.com/mmsegmentation/v0.5/swin/upernet_swin_small_patch4_window7_512x512_160k_ade20k_pretrain_224x224_1K/upernet_swin_small_patch4_window7_512x512_160k_ade20k_pretrain_224x224_1K_20210526_192015-ee2fff1c.pth",
        "upernet-swin-base": "https://download.openmmlab.com/mmsegmentation/v0.5/swin/upernet_swin_base_patch4_window12_512x512_160k_ade20k_pretrain_384x384_22K/upernet_swin_base_patch4_window12_512x512_160k_ade20k_pretrain_384x384_22K_20210531_125459-429057bf.pth",
        "upernet-swin-large": "https://download.openmmlab.com/mmsegmentation/v0.5/swin/upernet_swin_large_patch4_window12_512x512_pretrain_384x384_22K_160k_ade20k/upernet_swin_large_patch4_window12_512x512_pretrain_384x384_22K_160k_ade20k_20220318_091743-9ba68901.pth",
    }
    checkpoint_url = model_name_to_url[model_name]
    state_dict = torch.hub.load_state_dict_from_url(checkpoint_url, map_location="cpu", file_name=model_name)[
        "state_dict"
    ]

    for name, param in state_dict.items():
        print(name, param.shape)

    config = get_upernet_config(model_name)
    model = UperNetForSemanticSegmentation(config)
    model.eval()

    # replace "bn" => "batch_norm"
    for key in state_dict.copy():
        val = state_dict.pop(key)
        if "bn" in key:
            key = key.replace("bn", "batch_norm")
        state_dict[key] = val

    # rename keys
    rename_keys = create_rename_keys(config)
    for src, dest in rename_keys:
        rename_key(state_dict, src, dest)
    read_in_q_k_v(state_dict, config.backbone_config)

    # fix downsample parameters
    for key, value in state_dict.items():
        if "downsample" in key:
            if "reduction" in key:
                state_dict[key] = reverse_correct_unfold_reduction_order(value)
            if "norm" in key:
                state_dict[key] = reverse_correct_unfold_norm_order(value)

    model.load_state_dict(state_dict)

    # verify on image
    url = "https://huggingface.co/datasets/hf-internal-testing/fixtures_ade20k/resolve/main/ADE_val_00000001.jpg"
    with httpx.stream("GET", url) as response:
        image = Image.open(BytesIO(response.read())).convert("RGB")

    processor = SegformerImageProcessor()
    pixel_values = processor(image, return_tensors="pt").pixel_values

    with torch.no_grad():
        outputs = model(pixel_values)
        logits = outputs.logits

    print(logits.shape)
    print("First values of logits:", logits[0, 0, :3, :3])
    # assert values
    if model_name == "upernet-swin-tiny":
        expected_slice = torch.tensor(
            [[-7.5958, -7.5958, -7.4302], [-7.5958, -7.5958, -7.4302], [-7.4797, -7.4797, -7.3068]]
        )
    elif model_name == "upernet-swin-small":
        expected_slice = torch.tensor(
            [[-7.1921, -7.1921, -6.9532], [-7.1921, -7.1921, -6.9532], [-7.0908, -7.0908, -6.8534]]
        )
    elif model_name == "upernet-swin-base":
        expected_slice = torch.tensor(
            [[-6.5851, -6.5851, -6.4330], [-6.5851, -6.5851, -6.4330], [-6.4763, -6.4763, -6.3254]]
        )
    elif model_name == "upernet-swin-large":
        expected_slice = torch.tensor(
            [[-7.5297, -7.5297, -7.3802], [-7.5297, -7.5297, -7.3802], [-7.4044, -7.4044, -7.2586]]
        )
    print("Logits:", outputs.logits[0, 0, :3, :3])
    assert torch.allclose(outputs.logits[0, 0, :3, :3], expected_slice, atol=1e-4)
    print("Looks ok!")

    if pytorch_dump_folder_path is not None:
        print(f"Saving model {model_name} to {pytorch_dump_folder_path}")
        model.save_pretrained(pytorch_dump_folder_path)
        print(f"Saving processor to {pytorch_dump_folder_path}")
        processor.save_pretrained(pytorch_dump_folder_path)

    if push_to_hub:
        print(f"Pushing model and processor for {model_name} to hub")
        model.push_to_hub(f"openmmlab/{model_name}")
        processor.push_to_hub(f"openmmlab/{model_name}")