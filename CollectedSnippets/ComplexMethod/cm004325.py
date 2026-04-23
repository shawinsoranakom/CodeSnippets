def write_model(input_dir, output_dir):
    """Convert NanoChat model from original checkpoint format to HuggingFace format."""
    print("Converting the model.")
    os.makedirs(output_dir, exist_ok=True)

    input_path = Path(input_dir)

    # Load config
    config = load_config_from_checkpoint(input_path)
    print(f"Loaded config hidden_size={config.hidden_size} num_layers={config.num_hidden_layers}")

    # Load checkpoint - try model_*.pt first, then pytorch_model.bin
    checkpoint_files = list(input_path.glob("model_*.pt"))
    if checkpoint_files:
        checkpoint_path = checkpoint_files[0]
    else:
        checkpoint_path = input_path / "pytorch_model.bin"

    print(f"Fetching all parameters from the checkpoint at {checkpoint_path}...")
    old_state = torch.load(checkpoint_path, map_location="cpu")

    # Original nanochat weights are in bfloat16
    for key in old_state:
        if old_state[key].dtype == torch.float32:
            old_state[key] = old_state[key].to(torch.bfloat16)

    # Infer key-value heads from checkpoint
    inferred_kv = infer_kv_heads(config, old_state)
    config.num_key_value_heads = inferred_kv
    if config.num_attention_heads % config.num_key_value_heads != 0:
        print(f"Adjusting num_attention_heads from {config.num_attention_heads} to {config.num_key_value_heads}")
        config.num_attention_heads = config.num_key_value_heads

    print("Converting model...")
    state_dict = {}
    rename_map = {}

    def assign(
        old_key: str,
        new_key: str,
        old_state: dict[str, torch.Tensor],
        state_dict: dict[str, torch.Tensor],
        rename_map: dict[str, str],
    ) -> None:
        tensor = old_state.get(old_key)
        if tensor is None:
            return
        state_dict[new_key] = tensor.clone()
        rename_map[old_key] = new_key

    # Convert embeddings and head
    assign("transformer.wte.weight", "model.embed_tokens.weight", old_state, state_dict, rename_map)
    assign("lm_head.weight", "lm_head.weight", old_state, state_dict, rename_map)

    # Convert layers
    for layer_idx in range(config.num_hidden_layers):
        old_prefix = f"transformer.h.{layer_idx}"
        new_prefix = f"model.layers.{layer_idx}"
        mapping = convert_layer(old_prefix, new_prefix)
        for old_key, new_key in mapping.items():
            assign(old_key, new_key, old_state, state_dict, rename_map)

    missing = [key for key in old_state.keys() if key not in rename_map]
    if missing:
        print(f"Skipped {len(missing)} legacy entries that have no equivalent in the shared implementation")

    del old_state
    gc.collect()

    # Update config
    config.torch_dtype = torch.bfloat16
    config.tie_word_embeddings = False

    # Load the checkpoint into the model
    print("Loading the checkpoint in a NanoChat model.")
    with torch.device("meta"):
        model = NanoChatForCausalLM(config)
    model.load_state_dict(state_dict, strict=True, assign=True)
    print("Checkpoint loaded successfully.")

    if hasattr(model.config, "_name_or_path"):
        del model.config._name_or_path

    print("Saving the model.")
    model.save_pretrained(output_dir)
    del state_dict, model

    # Safety check: reload the converted model
    gc.collect()
    print("Reloading the model to check if it's saved correctly.")
    NanoChatForCausalLM.from_pretrained(output_dir, torch_dtype=torch.bfloat16, device_map="auto")
    print("Model reloaded successfully.")