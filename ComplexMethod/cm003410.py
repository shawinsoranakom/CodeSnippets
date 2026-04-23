def write_model(
    model_path: str,
    input_base_path: str,
    include_tokenizer: bool = True,
    tokenizer_id: str | None = None,
    max_sequence_length: int | None = None,
    dtype: torch.dtype = torch.bfloat16,
    device: str | None = None,
):
    """
    Convert OLMo Hybrid checkpoint to HuggingFace format.

    Args:
        model_path: Output directory for the HuggingFace model.
        input_base_path: Path to the OLMo checkpoint directory containing config.json and model_and_optim/.
        include_tokenizer: Whether to save the tokenizer alongside the model.
        tokenizer_id: HuggingFace tokenizer identifier. Defaults to the one in the config.
        max_sequence_length: Override for max sequence length. If None, read from config.
        dtype: Torch dtype for the output model weights.
        device: Device to use for loading/conversion (e.g., "cpu", "cuda"). Defaults to CPU.
    """
    os.makedirs(model_path, exist_ok=True)

    config_path = Path(input_base_path) / "config.json"
    olmo_config = json.loads(config_path.read_text())
    model_config = olmo_config["model"]
    block_config = model_config["block"]
    attention_config = block_config.get("attention", {})
    fla_config = block_config.get("fla", {})
    tokenizer_config = olmo_config["dataset"]["tokenizer"]

    n_layers = model_config["n_layers"]
    n_heads = attention_config.get("n_heads", model_config.get("n_heads", 32))
    n_kv_heads = attention_config.get("n_kv_heads", n_heads)
    dim = model_config["d_model"]

    rope_config = attention_config.get("rope")

    if rope_config is not None:
        rope_theta = rope_config.get("theta", 500000.0)

        # Build unified rope_parameters dict
        rope_parameters = {"rope_theta": rope_theta}

        rope_scaling_config = rope_config.get("scaling")
        if rope_scaling_config:
            if hasattr(rope_scaling_config, "to_hf_config"):
                rope_parameters.update(rope_scaling_config.to_hf_config())
            else:
                rope_parameters.update(rope_scaling_config)
        else:
            rope_parameters["rope_type"] = "default"
    else:
        rope_parameters = None

    # Resolve max_position_embeddings with priority:
    # CLI arg > train_module.max_sequence_length > dataset.sequence_length > fallback
    if max_sequence_length is None:
        max_sequence_length = olmo_config.get("train_module", {}).get("max_sequence_length")
    if max_sequence_length is None:
        max_sequence_length = olmo_config.get("dataset", {}).get("sequence_length")
    if max_sequence_length is None:
        max_sequence_length = 65536
        print(f"Warning: max_sequence_length not found in config or CLI, using default: {max_sequence_length}")

    max_position_embeddings = max_sequence_length

    layer_types = get_layer_types_from_config(olmo_config)

    fla_layer_kwargs = fla_config.get("fla_layer_kwargs", {})
    linear_key_head_dim = fla_layer_kwargs.get("head_dim", 96)
    linear_value_head_dim = fla_layer_kwargs.get("head_v_dim", linear_key_head_dim * 2)
    linear_num_heads = fla_layer_kwargs.get("num_heads", n_heads)
    linear_conv_kernel_dim = fla_layer_kwargs.get("conv_kernel_dim", 4)
    linear_allow_neg_eigval = fla_layer_kwargs.get("allow_neg_eigval", True)

    print(f"Fetching all parameters from the checkpoint at {input_base_path}.")

    loaded = load_model(os.path.join(input_base_path, "model_and_optim"))["model"]
    print(f"Loaded {len(loaded)} keys from checkpoint")

    param_count = 0
    full_state_dict: dict[str, torch.Tensor] = {}

    for layer_i in range(n_layers):
        layer_type = layer_types[layer_i]

        if layer_type == "linear_attention":
            layer_state = convert_fla_layer_weights(loaded, layer_i)
        else:
            layer_state = convert_attention_layer_weights(loaded, layer_i)

        full_state_dict.update(layer_state)
        param_count += sum(v.numel() for v in layer_state.values())
        print(f"Converted layer {layer_i} ({layer_type})")

    # Add embeddings and lm_head
    full_state_dict["model.embed_tokens.weight"] = loaded["embeddings.weight"]
    full_state_dict["model.norm.weight"] = loaded["lm_head.norm.weight"]
    full_state_dict["lm_head.weight"] = loaded["lm_head.w_out.weight"]
    param_count += sum(
        v.numel() for v in [loaded["embeddings.weight"], loaded["lm_head.norm.weight"], loaded["lm_head.w_out.weight"]]
    )

    # Cast all tensors to target dtype (matches OLMo-core behavior which casts everything,
    # including buffers like A_log and dt_bias)
    full_state_dict = {k: v.to(dtype) if torch.is_tensor(v) else v for k, v in full_state_dict.items()}

    print(f"Total parameters: {param_count}")

    config = OlmoHybridConfig(
        vocab_size=model_config["vocab_size"],
        hidden_size=dim,
        intermediate_size=block_config["feed_forward"]["hidden_size"],
        num_hidden_layers=n_layers,
        num_attention_heads=n_heads,
        num_key_value_heads=n_kv_heads,
        max_position_embeddings=max_position_embeddings,
        pad_token_id=tokenizer_config.get("pad_token_id"),
        bos_token_id=tokenizer_config.get("bos_token_id"),
        eos_token_id=tokenizer_config.get("eos_token_id"),
        tie_word_embeddings=False,
        rms_norm_eps=block_config.get("layer_norm", {}).get("eps", 1e-6),
        rope_parameters=rope_parameters,
        layer_types=layer_types,
        linear_num_key_heads=linear_num_heads,
        linear_num_value_heads=linear_num_heads,
        linear_key_head_dim=linear_key_head_dim,
        linear_value_head_dim=linear_value_head_dim,
        linear_conv_kernel_dim=linear_conv_kernel_dim,
        linear_allow_neg_eigval=linear_allow_neg_eigval,
    )
    if rope_parameters is None:
        config.rope_parameters = None
        config.rope_theta = None

    # Explicitly set architectures (normally set by model.save_pretrained, but we
    # save directly without the model roundtrip)
    config.architectures = ["OlmoHybridForCausalLM"]

    # Save config and weights directly (no from_pretrained roundtrip, which can
    # corrupt embeddings and fail to cast buffers like A_log)
    config.save_pretrained(model_path)

    from safetensors.torch import save_file

    safetensors_path = os.path.join(model_path, "model.safetensors")
    save_file(full_state_dict, safetensors_path)
    print(f"Saved weights to {safetensors_path}")

    del full_state_dict
    del loaded
    gc.collect()

    if include_tokenizer:
        tokenizer_id = tokenizer_id or tokenizer_config.get("identifier")
        if tokenizer_id:
            _write_tokenizer(model_path, tokenizer_id, max_sequence_length, tokenizer_config)

    # Update config with tokenizer info
    hf_config_path = Path(model_path) / "config.json"
    with open(hf_config_path, "r") as f:
        config_dict = json.load(f)

    config_dict["max_position_embeddings"] = max_position_embeddings
    config_dict["pad_token_id"] = tokenizer_config.get("pad_token_id")
    config_dict["bos_token_id"] = tokenizer_config.get("bos_token_id")
    config_dict["eos_token_id"] = tokenizer_config.get("eos_token_id")

    with open(hf_config_path, "w") as f:
        json.dump(config_dict, f, indent=2)
    print("Updated config.json with tokenizer settings")