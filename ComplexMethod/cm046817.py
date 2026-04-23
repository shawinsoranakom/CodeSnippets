def test_save_merged_16bit(model, tokenizer, temp_save_dir: str):
    save_path = os.path.join(
        temp_save_dir,
        "unsloth_merged_16bit",
        model.config._name_or_path.replace("/", "_"),
    )

    model.save_pretrained_merged(
        save_path, tokenizer = tokenizer, save_method = "merged_16bit"
    )

    # Check model files
    assert os.path.isdir(save_path), f"Directory {save_path} does not exist."
    assert os.path.isfile(
        os.path.join(save_path, "config.json")
    ), "config.json not found."

    weight_files = [
        f
        for f in os.listdir(save_path)
        if f.endswith(".bin") or f.endswith(".safetensors")
    ]
    assert len(weight_files) > 0, "No weight files found in the save directory."

    # Check tokenizer files
    for file in tokenizer_files:
        assert os.path.isfile(
            os.path.join(save_path, file)
        ), f"{file} not found in the save directory."

    # Check config to see if it is 16bit by checking for quantization config
    config_path = os.path.join(save_path, "config.json")
    with open(config_path, "r") as f:
        config = json.load(f)

    assert (
        "quantization_config" not in config
    ), "Quantization config not found in the model config."

    # Store the size of the model files
    total_size = sum(os.path.getsize(os.path.join(save_path, f)) for f in weight_files)
    save_file_sizes["merged_16bit"][model.config._name_or_path] = total_size
    print(f"Total size of merged_16bit files: {total_size} bytes")

    # Test loading the model from the saved path
    loaded_model, loaded_tokenizer = FastLanguageModel.from_pretrained(
        save_path,
        max_seq_length = 128,
        dtype = None,
        load_in_4bit = True,
    )