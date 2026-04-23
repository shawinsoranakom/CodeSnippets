def convert_and_write_model(input_dir: str, output_dir: str, max_position_embeddings: int, modules_are_split: bool):
    """Convert the model and save it (this implicitly save the config as well)."""
    params = read_json(os.path.join(input_dir, "params.json"))
    config = convert_config(params, max_position_embeddings)

    full_state_dict = {}
    # The model may be split between different files, but a single nn.Module is always fully present in a single file
    if not modules_are_split:
        shards = [file for file in os.listdir(input_dir) if file.endswith(".safetensors")]
        for shard_file in shards:
            original_state_dict = load_file(os.path.join(input_dir, shard_file))
            new_dict = convert_state_dict(original_state_dict, config)
            full_state_dict.update(new_dict)
    # A single nn.Module is split between different checkpoint files
    else:
        shards = [file for file in os.listdir(input_dir) if re.match(r"consolidated.\d+.pth", file)]
        shards = sorted(shards, key=lambda x: int(x.split(".")[1]))
        loaded_shards = [
            torch.load(os.path.join(input_dir, file), map_location="cpu", weights_only=True) for file in shards
        ]
        full_state_dict = convert_state_dict_sharded(loaded_shards, config)

    # Load weights into model and resave them
    with torch.device("meta"):
        model = MistralForCausalLM(config)
    model.load_state_dict(full_state_dict, strict=True, assign=True)
    model.save_pretrained(output_dir)