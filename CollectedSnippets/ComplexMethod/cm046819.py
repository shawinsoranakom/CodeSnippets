def test_save_torchao(fp16_model_tokenizer, temp_save_dir: str):
    model, tokenizer = fp16_model_tokenizer
    save_path = os.path.join(
        temp_save_dir, "unsloth_torchao", model.config._name_or_path.replace("/", "_")
    )

    from torchao.quantization import Int8DynamicActivationInt8WeightConfig

    torchao_config = Int8DynamicActivationInt8WeightConfig()
    model.save_pretrained_torchao(
        save_path,
        tokenizer = tokenizer,
        torchao_config = torchao_config,
        push_to_hub = False,
    )

    weight_files_16bit = [
        f
        for f in os.listdir(save_path)
        if f.endswith(".bin") or f.endswith(".safetensors")
    ]
    total_16bit_size = sum(
        os.path.getsize(os.path.join(save_path, f)) for f in weight_files_16bit
    )
    save_file_sizes["merged_16bit"][model.config._name_or_path] = total_16bit_size

    torchao_save_path = save_path + "-torchao"

    # Check model files
    assert os.path.isdir(
        torchao_save_path
    ), f"Directory {torchao_save_path} does not exist."
    assert os.path.isfile(
        os.path.join(torchao_save_path, "config.json")
    ), "config.json not found."

    weight_files = [
        f
        for f in os.listdir(torchao_save_path)
        if f.endswith(".bin") or f.endswith(".safetensors")
    ]
    assert len(weight_files) > 0, "No weight files found in the save directory."

    # Check tokenizer files
    for file in tokenizer_files:
        assert os.path.isfile(
            os.path.join(torchao_save_path, file)
        ), f"{file} not found in the save directory."

    # Store the size of the model files
    total_size = sum(
        os.path.getsize(os.path.join(torchao_save_path, f)) for f in weight_files
    )
    save_file_sizes["torchao"][model.config._name_or_path] = total_size

    assert (
        total_size < save_file_sizes["merged_16bit"][model.config._name_or_path]
    ), "torchao files are larger than merged 16bit files."

    # Check config to see if it is quantized with torchao
    config_path = os.path.join(torchao_save_path, "config.json")
    with open(config_path, "r") as f:
        config = json.load(f)

    assert (
        "quantization_config" in config
    ), "Quantization config not found in the model config."

    # Test loading the model from the saved path
    # can't set `load_in_4bit` to True because the model is torchao quantized
    # can't quantize again with bitsandbytes
    import torch.serialization

    with torch.serialization.safe_globals([getattr]):
        loaded_model, loaded_tokenizer = FastModel.from_pretrained(
            torchao_save_path,
            max_seq_length = 128,
            dtype = None,
            load_in_4bit = False,
        )