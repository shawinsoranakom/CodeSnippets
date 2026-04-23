def convert_mamba_ssm_checkpoint_file_to_huggingface_model_file(
    mamba_ssm_checkpoint_path: str,
    precision: str,
    output_dir: str,
    tokenizer_path: str | None = None,
    save_model: bool | str = True,
) -> None:
    # load tokenizer if provided, this will be used to set the
    # token_ids in the config file
    token_ids = {}
    if tokenizer_path:
        tokenizer = AutoTokenizer.from_pretrained(tokenizer_path)
        for key in [
            "bos_token_id",
            "eos_token_id",
            "pad_token_id",
        ]:
            id = getattr(tokenizer, key, None)
            if id:
                token_ids[key] = id

    # there are some configs unsettable by mamba_ssn config, so
    # if there are changes from the defaults, have to pass them into
    # the function
    unsettables = {
        "mamba_d_head": 64,
        "mamba_d_state": 128,
        "mamba_n_groups": 1,
        "rms_norm_eps": 1e-5,
    }

    # Load and save config based on name
    config_path = path.join(mamba_ssm_checkpoint_path, "config.json")
    with open(config_path, "r", encoding="utf-8") as json_file:
        config = json.load(json_file)

    # convert the config
    hf_config = convert_ssm_config_to_hf_config(
        config_ssm=config,
        **token_ids,
        **unsettables,
    )
    hf_config.save_pretrained(output_dir)

    # Load state dict of the original model and transfer to hf model
    state_dict = torch.load(
        path.join(mamba_ssm_checkpoint_path, "pytorch_model.bin"),
        map_location="cpu",
        weights_only=True,
    )
    # FIXME: allow other parameters to pass in
    state_dict = convert_state_dict_from_mamba_ssm(state_dict)

    # Save new model to pytorch_dump_path
    dtype = torch.float32 if precision == "fp32" else (torch.bfloat16 if precision == "bf16" else torch.float16)

    save_file_fn = None
    if isinstance(save_model, bool) and save_model:
        save_file_fn = save_single_safetensor
    elif isinstance(save_model, str) and save_model == "sharded":
        save_file_fn = save_sharded_safetensors

    if save_file_fn:
        save_file_fn({k: v.to(dtype) for k, v in state_dict.items()}, output_dir, metadata={"format": "pt"})