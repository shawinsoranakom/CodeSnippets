def merge_configurations(config_path: str, entropy_params_path: str) -> dict[str, Any]:
    logger.info("Merging configurations")

    with open(config_path, "r") as f:
        main_config = json.load(f)

    with open(entropy_params_path, "r") as f:
        entropy_data = json.load(f)

    entropy_model_params = entropy_data.get("entropy_model", {})
    patcher_args = entropy_data.get("data", {}).get("patcher_args", {})

    unified_config = main_config.copy()["args"]

    for key in ["vocab_size", "dim", "n_layers", "n_heads", "max_seqlen"]:
        if key in unified_config and not isinstance(unified_config[key], int):
            unified_config[key] = int(unified_config[key])

    patch_size = patcher_args.get("patch_size", 8)
    if isinstance(patch_size, float):
        patch_size = int(patch_size)

    # Create patcher config
    patcher_hidden_size = int(entropy_model_params.get("dim", 512))
    patcher_multiple_of = int(entropy_model_params.get("multiple_of", 256))
    patcher_intermediate_size = patcher_multiple_of * (
        (int(8 * patcher_hidden_size / 3) + patcher_multiple_of - 1) // patcher_multiple_of
    )

    patcher_config = {
        "vocab_size": int(entropy_model_params.get("vocab_size", 256)),
        "hidden_size": patcher_hidden_size,
        "num_hidden_layers": int(entropy_model_params.get("n_layers", 8)),
        "num_attention_heads": int(entropy_model_params.get("n_heads", 8)),
        "num_key_value_heads": int(entropy_model_params.get("n_kv_heads"))
        if entropy_model_params.get("n_kv_heads") is not None
        else None,
        "max_position_embeddings": int(entropy_model_params.get("max_seqlen", 1024)),
        "norm_eps": entropy_model_params.get("norm_eps", 1e-5),
        "dropout": entropy_model_params.get("dropout", 0.0),
        "rope_theta": entropy_model_params.get("rope_theta", 10000.0),
        "attn_impl": entropy_model_params.get("attn_impl", "sdpa"),
        "attn_bias_type": entropy_model_params.get("attn_bias_type", "causal"),
        "intermediate_size": patcher_intermediate_size,
    }

    # Create encoder config
    encoder_hidden_size = unified_config.get("dim_local_encoder", 1024)
    encoder_multiple_of = unified_config.get("multiple_of", 256)
    encoder_intermediate_size = encoder_multiple_of * (
        (int(8 * encoder_hidden_size / 3) + encoder_multiple_of - 1) // encoder_multiple_of
    )

    encoder_config = {
        "vocab_size": unified_config.get("vocab_size", 256),
        "cross_attn_all_layers": unified_config.get("cross_attn_all_layers_encoder", False),
        "cross_attn_k": unified_config.get("cross_attn_k", 2),
        "hidden_size_global": unified_config.get("dim_global", 2048),
        "pm_size": unified_config.get("pm_size", 0),
        "hidden_size": encoder_hidden_size,
        "num_attention_heads": unified_config.get("n_heads_local_encoder", 16),
        "num_key_value_heads": unified_config.get("n_kv_heads"),
        "num_hidden_layers": unified_config.get("n_layers_local_encoder", 1),
        "norm_eps": unified_config.get("norm_eps", 1e-5),
        "dropout": unified_config.get("dropout", 0.0),
        "max_position_embeddings": unified_config.get("max_encoder_seq_length")
        or unified_config.get("max_seqlen", 1024),
        "rope_theta": unified_config.get("rope_theta", 10000.0),
        "rope_parameters": {"rope_type": "default"},
        "hidden_act": unified_config.get("hidden_act", "silu"),
        "_attn_implementation": unified_config.get("_attn_implementation", "sdpa"),
        "intermediate_size": encoder_intermediate_size,
    }

    # Create decoder config
    decoder_hidden_size = unified_config.get("dim_local_decoder", 1024)
    decoder_multiple_of = unified_config.get("multiple_of", 256)
    decoder_intermediate_size = decoder_multiple_of * (
        (int(8 * decoder_hidden_size / 3) + decoder_multiple_of - 1) // decoder_multiple_of
    )

    decoder_config = {
        "vocab_size": unified_config.get("vocab_size", 256),
        "cross_attn_all_layers": unified_config.get("cross_attn_all_layers_decoder", False),
        "cross_attn_k": unified_config.get("cross_attn_k", 2),
        "hidden_size_global": unified_config.get("dim_global", 2048),
        "hidden_size": decoder_hidden_size,
        "num_attention_heads": unified_config.get("n_heads_local_decoder", 16),
        "num_key_value_heads": unified_config.get("n_kv_heads"),
        "num_hidden_layers": unified_config.get("n_layers_local_decoder", 9),
        "norm_eps": unified_config.get("norm_eps", 1e-5),
        "dropout": unified_config.get("dropout", 0.0),
        "max_position_embeddings": unified_config.get("max_encoder_seq_length")
        or unified_config.get("max_seqlen", 1024),
        "rope_theta": unified_config.get("rope_theta", 10000.0),
        "rope_parameters": {"rope_type": "default"},
        "hidden_act": unified_config.get("hidden_act", "silu"),
        "_attn_implementation": unified_config.get("_attn_implementation", "sdpa"),
        "intermediate_size": decoder_intermediate_size,
    }

    # Create global transformer config
    global_hidden_size = unified_config.get("dim_global", 2048)
    global_multiple_of = unified_config.get("multiple_of", 256)
    global_intermediate_size = global_multiple_of * (
        (int(8 * global_hidden_size / 3) + global_multiple_of - 1) // global_multiple_of
    )

    global_config = {
        "hidden_size": global_hidden_size,
        "num_attention_heads": unified_config.get("n_heads_global", 16),
        "num_key_value_heads": unified_config.get("n_kv_heads_global"),
        "num_hidden_layers": unified_config.get("n_layers_global", 25),
        "norm_eps": unified_config.get("norm_eps", 1e-5),
        "dropout": unified_config.get("dropout", 0.0),
        "max_position_embeddings": unified_config.get("max_seqlen", 1024),
        "rope_theta": unified_config.get("rope_theta", 10000.0),
        "rope_parameters": {"rope_type": "default"},
        "hidden_act": unified_config.get("hidden_act", "silu"),
        "_attn_implementation": unified_config.get("_attn_implementation", "sdpa"),
        "intermediate_size": global_intermediate_size,
    }

    # Create main config with sub-configs
    main_config_dict = {
        "model_type": "blt",
        "vocab_size": unified_config.get("vocab_size", 256),
        "max_position_embeddings": unified_config.get("max_seqlen", 1024),
        "patch_in_forward": True,
        "realtime_patching": True,
        "patching_mode": "entropy",
        "patch_size": patch_size,
        "patching_threshold": patcher_args.get("threshold", 0.5),
        "patching_threshold_add": patcher_args.get("threshold_add", 0.0),
        "max_patch_length": patcher_args.get("max_patch_length"),
        "patching_batch_size": patcher_args.get("patching_batch_size", 1),
        "patching_device": patcher_args.get("patching_device", "cuda"),
        "monotonicity": patcher_args.get("monotonicity", False),
        "cross_attn_k": unified_config.get("cross_attn_k", 2),
        "encoder_hash_byte_group_size": unified_config.get("encoder_hash_byte_group_size"),
        "encoder_hash_byte_group_vocab": unified_config.get("encoder_hash_byte_group_vocab", 30000),
        "encoder_hash_byte_group_nb_functions": unified_config.get("encoder_hash_byte_group_nb_functions", 3),
        "pm_size": unified_config.get("pm_size", 0),
        "patcher_config": patcher_config,
        "encoder_config": encoder_config,
        "decoder_config": decoder_config,
        "global_config": global_config,
    }

    main_config_dict["tie_word_embeddings"] = False

    logger.info(f"Merged configuration with {len(main_config_dict)} parameters")
    return main_config_dict