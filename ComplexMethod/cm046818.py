def test_save_merged_4bit(model, tokenizer, temp_save_dir: str):
    save_path = os.path.join(
        temp_save_dir,
        "unsloth_merged_4bit",
        model.config._name_or_path.replace("/", "_"),
    )

    model.save_pretrained_merged(
        save_path, tokenizer = tokenizer, save_method = "merged_4bit_forced"
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

    # Store the size of the model files
    total_size = sum(os.path.getsize(os.path.join(save_path, f)) for f in weight_files)
    save_file_sizes["merged_4bit"][model.config._name_or_path] = total_size

    print(f"Total size of merged_4bit files: {total_size} bytes")

    assert (
        total_size < save_file_sizes["merged_16bit"][model.config._name_or_path]
    ), "Merged 4bit files are larger than merged 16bit files."

    # Check config to see if it is 4bit
    config_path = os.path.join(save_path, "config.json")
    with open(config_path, "r") as f:
        config = json.load(f)

    assert (
        "quantization_config" in config
    ), "Quantization config not found in the model config."

    # Test loading the model from the saved path
    loaded_model, loaded_tokenizer = FastModel.from_pretrained(
        save_path,
        max_seq_length = 128,
        dtype = None,
        load_in_4bit = True,
    )