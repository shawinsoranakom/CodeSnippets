def convert_checkpoint(checkpoint_path, config_path, pytorch_dump_folder_path=None, push_to_hub=None):
    # load config yaml file
    with open(config_path, "r") as f:
        model_config = yaml.safe_load(f)

    # extra relevant parameters
    ratios = model_config["generator"]["config"]["ratios"]
    target_bandwidths = model_config["generator"]["config"]["target_bandwidths"]
    sample_rate = model_config["generator"]["config"]["sample_rate"]
    acoustic_model_config = {
        "encoder_hidden_size": 64,
        "decoder_hidden_size": 1024,
        # NOTE: original DAC uses [2, 4, 8, 8] `downsampling ratios`, namely reverse of `upsampling_ratios`
        # (not sure if intentional by Xcodec but we keep it)
        "downsampling_ratios": ratios,
        "upsampling_ratios": ratios,
        "sampling_rate": sample_rate,
        "hidden_size": model_config["generator"]["config"]["D"],
    }
    semantic_model = model_config["generator"]["config"]["semantic_techer"]
    if semantic_model == "hubert_base":
        semantic_model_config = AutoConfig.from_pretrained("facebook/hubert-base-ls960")
    elif semantic_model == "wavlm_base_plus":
        semantic_model_config = AutoConfig.from_pretrained("microsoft/wavlm-base-plus")
    elif semantic_model == "hubert_base_general":
        semantic_model_config = AutoConfig.from_pretrained("ZhenYe234/hubert_base_general_audio")
    else:
        raise ValueError(f"Unknown semantic model: {semantic_model}")

    config = XcodecConfig(
        target_bandwidths=target_bandwidths,
        acoustic_model_config=acoustic_model_config,
        semantic_model_config=semantic_model_config,
        sample_rate=sample_rate,
        codebook_size=model_config["generator"]["config"]["bins"],
    )

    # create model
    if not torch.cuda.is_available():
        raise ValueError("Run this script on a machine with a GPU for weight norm layers to be correctly copied.")
    torch_device = "cuda"
    model = XcodecModel(config).to(torch_device)

    logger.info("Loading original checkpoint ...")

    state_dict = safe_load(checkpoint_path)

    # the original checkpoint has weight norm applied
    model.apply_weight_norm()

    logger.info("Converting model ...")

    new_state_dict = convert_old_keys_to_new_keys(state_dict)

    missing_keys, unexpected_keys = model.load_state_dict(new_state_dict, strict=True, assign=True)  # strict=False)

    if len(unexpected_keys) != 0:
        raise ValueError(f"Unexpected keys: {unexpected_keys}")

    if len(missing_keys) != 0:
        raise ValueError(f"missing keys found: {missing_keys}")

    model.remove_weight_norm()
    if pytorch_dump_folder_path is not None:
        model.save_pretrained(pytorch_dump_folder_path)

    feature_extractor = DacFeatureExtractor(
        sampling_rate=config.sample_rate,
        hop_length=config.acoustic_model_config.hop_length,
    )
    if pytorch_dump_folder_path is not None:
        feature_extractor.save_pretrained(pytorch_dump_folder_path)

    if push_to_hub:
        print("Pushing to the hub...")
        feature_extractor.push_to_hub(push_to_hub)
        model.push_to_hub(push_to_hub)