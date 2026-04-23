def convert_and_test_vjepa2_checkpoint(model_name, pytorch_dump_folder_path, push_to_hub=False):
    """
    Copy/paste/tweak model's weights to our VJEPA2 structure.
    """
    config = get_vjepa2_config(model_name)

    # load original model from torch hub
    original_encoder, original_predictor = torch.hub.load(HUB_REPO, "vjepa2_" + model_name, source=HUB_SOURCE)
    original_encoder.eval()
    original_predictor.eval()
    original_preprocessor = torch.hub.load(
        HUB_REPO, "vjepa2_preprocessor", source=HUB_SOURCE, crop_size=config.crop_size
    )

    # load state_dict of original model, remove and rename some keys
    encoder_state_dict = original_encoder.state_dict()
    decoder_state_dict = original_predictor.state_dict()

    model = VJEPA2Model(config).eval()
    state_dict = model.state_dict()

    og_encoder_sd = convert_encoder_keys(state_dict, encoder_state_dict, config)
    og_predictor_sd = convert_predictor_keys(state_dict, decoder_state_dict, config)

    og_state_dict = og_encoder_sd
    og_state_dict.update(og_predictor_sd)
    model.load_state_dict(og_state_dict)

    # load image
    image = prepare_img()
    image = torch.Tensor(np.array(image)).unsqueeze(0).permute(0, 3, 1, 2)
    print("Input shape: ", image.shape)

    crop_size = config.crop_size
    processor = VJEPA2VideoProcessor(crop_size=crop_size)
    pr_out = processor(image, return_tensors="pt")
    pixel_values_videos = pr_out.pixel_values_videos
    # run original preprocessor
    original_pixel_values = original_preprocessor(image)
    assert original_pixel_values[0].permute(1, 0, 2, 3).shape == pixel_values_videos[0].shape
    assert torch.allclose(original_pixel_values[0].permute(1, 0, 2, 3), pixel_values_videos[0], atol=1e-3)

    with torch.no_grad():
        # reshape and move to gpu
        if pixel_values_videos.size(1) == 1:
            pixel_values_videos = pixel_values_videos.repeat(1, config.frames_per_clip, 1, 1, 1)
        # pixel_values_videos = pixel_values_videos.permute(0, 2, 1, 3, 4)  # B x C x T x H x W
        pixel_values_videos = pixel_values_videos.to(device="cuda", dtype=torch.float32)
        original_encoder = original_encoder.to(device="cuda", dtype=torch.float32)
        original_predictor = original_predictor.to(device="cuda", dtype=torch.float32)
        model = model.to(device="cuda", dtype=torch.float32)
        # forward
        original_encoder_outputs = original_encoder(pixel_values_videos.permute(0, 2, 1, 3, 4))
        B, N, _ = original_encoder_outputs.shape
        # test full mask
        context_mask = [torch.arange(N, device=pixel_values_videos.device).unsqueeze(0).repeat((B, 1))]
        predictor_mask = context_mask
        original_predictor_outputs = original_predictor(original_encoder_outputs, context_mask, predictor_mask)
        outputs = model(pixel_values_videos, context_mask=context_mask, target_mask=predictor_mask)
        assert torch.allclose(outputs.last_hidden_state, original_encoder_outputs, atol=1e-3)
        predictor_outputs = outputs.predictor_output
        assert torch.allclose(predictor_outputs.last_hidden_state, original_predictor_outputs, atol=1e-3)
        # test partial mask
        window_size = 256
        mask = torch.arange(N, device=pixel_values_videos.device).unsqueeze(0)
        context_mask = [mask[:, :window_size].repeat((B, 1))]
        predictor_mask = [mask[:, window_size : window_size * 2].repeat((B, 1))]
        original_predictor_outputs = original_predictor(
            apply_masks(original_encoder_outputs, context_mask),
            context_mask,
            predictor_mask,
        )
        outputs = model(pixel_values_videos, context_mask=context_mask, target_mask=predictor_mask)
        assert torch.allclose(outputs.last_hidden_state, original_encoder_outputs, atol=1e-3)
        predictor_outputs = outputs.predictor_output
        assert torch.allclose(predictor_outputs.last_hidden_state, original_predictor_outputs, atol=1e-3)

    print("Looks ok!")

    if pytorch_dump_folder_path is not None:
        Path(pytorch_dump_folder_path).mkdir(exist_ok=True)
        print(f"Saving model {model_name} to {pytorch_dump_folder_path}")
        model.save_pretrained(pytorch_dump_folder_path)
        print(f"Saving image processor to {pytorch_dump_folder_path}")
        processor.save_pretrained(pytorch_dump_folder_path)

    if push_to_hub:
        name = HUB_MODELS[model_name]
        model.push_to_hub(name, private=True)
        processor.push_to_hub(name, private=True)