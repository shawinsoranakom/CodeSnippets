def convert_config(original_config: dict, max_position_embeddings: int = 131072):
    original_audio_config = original_config.pop("multimodal")
    original_audio_config = original_audio_config["whisper_model_args"]["encoder_args"]
    original_text_config = original_config

    # Text config
    text_key_mapping = {
        "hidden_size": "dim",
        "num_hidden_layers": "n_layers",
        "intermediate_size": "hidden_dim",
        "num_attention_heads": "n_heads",
        "num_key_value_heads": "n_kv_heads",
        "rms_norm_eps": "norm_eps",
    }
    similar_text_keys_to_keep = [
        "head_dim",
        "vocab_size",
        "rope_theta",
    ]
    new_text_config_kwargs = {k: original_text_config[v] for k, v in text_key_mapping.items()}
    new_text_config_kwargs.update({k: v for k, v in original_text_config.items() if k in similar_text_keys_to_keep})
    # These are not always defined depending on `params.json`
    new_text_config_kwargs["sliding_window"] = original_text_config.get("sliding_window", None)
    new_text_config_kwargs["max_position_embeddings"] = original_text_config.get(
        "max_seq_len", max_position_embeddings
    )
    # This may sometimes be a string in `params.json`
    if new_text_config_kwargs["sliding_window"] is not None:
        new_text_config_kwargs["sliding_window"] = int(new_text_config_kwargs["sliding_window"])

    # Audio config
    audio_key_mapping = {
        "hidden_size": "dim",
        "num_hidden_layers": "n_layers",
        "intermediate_size": "hidden_dim",
        "num_attention_heads": "n_heads",
        "num_key_value_heads": "n_heads",
    }
    similar_audio_keys_to_keep = [
        "head_dim",
        "vocab_size",
        "rope_theta",
    ]
    new_audio_config_kwargs = {k: original_audio_config[v] for k, v in audio_key_mapping.items()}
    new_audio_config_kwargs.update({k: v for k, v in original_audio_config.items() if k in similar_audio_keys_to_keep})

    new_config = VoxtralRealtimeConfig(
        audio_config=new_audio_config_kwargs,
        text_config=new_text_config_kwargs,
        projector_hidden_act="gelu",
    )

    return new_config