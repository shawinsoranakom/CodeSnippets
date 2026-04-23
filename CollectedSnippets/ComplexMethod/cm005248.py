def _load_model(ckpt_path, device, use_small=False, model_type="text"):
    if model_type == "text":
        ModelClass = BarkSemanticModel
        ConfigClass = BarkSemanticConfig
        GenerationConfigClass = BarkSemanticGenerationConfig
    elif model_type == "coarse":
        ModelClass = BarkCoarseModel
        ConfigClass = BarkCoarseConfig
        GenerationConfigClass = BarkCoarseGenerationConfig
    elif model_type == "fine":
        ModelClass = BarkFineModel
        ConfigClass = BarkFineConfig
        GenerationConfigClass = BarkFineGenerationConfig
    else:
        raise NotImplementedError()
    model_key = f"{model_type}_small" if use_small else model_type
    model_info = REMOTE_MODEL_PATHS[model_key]
    if not os.path.exists(ckpt_path):
        logger.info(f"{model_type} model not found, downloading into `{CACHE_DIR}`.")
        _download(model_info["repo_id"], model_info["file_name"])
    checkpoint = torch.load(ckpt_path, map_location=device, weights_only=True)
    # this is a hack
    model_args = checkpoint["model_args"]
    if "input_vocab_size" not in model_args:
        model_args["input_vocab_size"] = model_args["vocab_size"]
        model_args["output_vocab_size"] = model_args["vocab_size"]
        del model_args["vocab_size"]

    # convert Bark model arguments to HF Bark model arguments
    model_args["num_heads"] = model_args.pop("n_head")
    model_args["hidden_size"] = model_args.pop("n_embd")
    model_args["num_layers"] = model_args.pop("n_layer")

    model_config = ConfigClass(**checkpoint["model_args"])
    model = ModelClass(config=model_config)
    model_generation_config = GenerationConfigClass()

    model.generation_config = model_generation_config
    state_dict = checkpoint["model"]
    # fixup checkpoint
    unwanted_prefix = "_orig_mod."
    for k in state_dict:
        if k.startswith(unwanted_prefix):
            # replace part of the key with corresponding layer name in HF implementation
            new_k = k[len(unwanted_prefix) :]
            for old_layer_name, new_layer_name in new_layer_name_dict.items():
                new_k = new_k.replace(old_layer_name, new_layer_name)

            state_dict[new_k] = state_dict.pop(k)

    extra_keys = set(state_dict.keys()) - set(model.state_dict().keys())
    extra_keys = {k for k in extra_keys if not k.endswith(".attn.bias")}
    missing_keys = set(model.state_dict().keys()) - set(state_dict.keys())
    missing_keys = {k for k in missing_keys if not k.endswith(".attn.bias")}
    if len(extra_keys) != 0:
        raise ValueError(f"extra keys found: {extra_keys}")
    if len(missing_keys) != 0:
        raise ValueError(f"missing keys: {missing_keys}")
    model.load_state_dict(state_dict, strict=False)
    n_params = model.num_parameters(exclude_embeddings=True)
    val_loss = checkpoint["best_val_loss"].item()
    logger.info(f"model loaded: {round(n_params / 1e6, 1)}M params, {round(val_loss, 3)} loss")
    model.eval()
    model.to(device)
    del checkpoint, state_dict

    return model