def load_config_from_checkpoint(input_path: Path) -> NanoChatConfig:
    """Load config from either meta_*.json or config.json in the checkpoint directory."""
    # Try to find meta_*.json first
    meta_files = list(input_path.glob("meta_*.json"))

    if meta_files:
        meta_file = meta_files[0]
        print(f"Loading config from {meta_file.name}")
        with open(meta_file, "r") as f:
            meta_config = json.load(f)

        # Extract model config from meta file
        if "model_config" in meta_config:
            model_config = meta_config["model_config"]
        else:
            model_config = meta_config

        # Map to NanoChat config parameters
        config_kwargs = {
            "vocab_size": model_config.get("vocab_size", 50304),
            "hidden_size": model_config.get("n_embd", 768),
            "num_hidden_layers": model_config.get("n_layer", 12),
            "num_attention_heads": model_config.get("n_head", 6),
            "num_key_value_heads": model_config.get("n_kv_head"),
            "max_position_embeddings": model_config.get("sequence_len", 2048),
            "intermediate_size": model_config.get("intermediate_size", model_config.get("n_embd", 768) * 4),
        }

        # Try to load existing config.json for additional parameters
        config_file = input_path / "config.json"
        if config_file.exists():
            print("Loading additional config from config.json")
            with open(config_file, "r") as f:
                extra_config = json.load(f)

            # Add additional parameters from config.json
            for key in [
                "hidden_act",
                "attention_dropout",
                "rms_norm_eps",
                "initializer_range",
                "logits_soft_cap",
                "attention_bias",
                "intermediate_size",
                "bos_token_id",
                "eos_token_id",
                "pad_token_id",
            ]:
                if key in extra_config:
                    config_kwargs[key] = extra_config[key]
                # Handle legacy qkv_bias -> attention_bias conversion
                elif key == "attention_bias" and "qkv_bias" in extra_config:
                    config_kwargs[key] = extra_config["qkv_bias"]

            # Handle rope_theta as a direct kwarg for the rope_parameters processing
            if "rope_theta" in extra_config:
                config_kwargs["rope_theta"] = extra_config["rope_theta"]

            # Handle rope_parameters or rope_scaling if present
            if "rope_parameters" in extra_config:
                config_kwargs["rope_parameters"] = extra_config["rope_parameters"]
            elif "rope_scaling" in extra_config and extra_config["rope_scaling"] is not None:
                config_kwargs["rope_parameters"] = extra_config["rope_scaling"]

        config = NanoChatConfig(**config_kwargs)
    else:
        # Fallback to loading from config.json if it exists
        config_file = input_path / "config.json"
        if config_file.exists():
            print("Loading config from config.json")
            config = NanoChatConfig.from_pretrained(input_path)
            # Handle legacy qkv_bias -> attention_bias conversion
            if hasattr(config, "qkv_bias") and not hasattr(config, "attention_bias"):
                config.attention_bias = config.qkv_bias
        else:
            raise ValueError(f"No config file found in {input_path}. Expected meta_*.json or config.json")

    return config