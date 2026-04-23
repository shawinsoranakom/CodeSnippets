def convert_state_dict(original_state_dict: dict, config: Mistral3Config):
    """Convert a state dict file, when a single `nn.Module` is never sharded in different files (usual case)."""
    new_dict = {}

    is_vision = isinstance(config, Mistral3Config)
    mapping = get_sd_mapping(is_vision)
    for old_key, tensor in original_state_dict.items():
        if "fake_quantizer" in old_key:
            continue

        new_key = map_old_key_to_new(old_key, mapping)

        if "vision" in old_key:
            num_attention_heads = config.vision_config.num_attention_heads
            num_key_value_heads = num_attention_heads
            hidden_size = config.vision_config.hidden_size
            head_dim = config.vision_config.head_dim
            key_value_dim = head_dim * num_attention_heads
            query_dim = head_dim * num_attention_heads
        else:
            text_config = config.text_config if is_vision else config
            num_attention_heads = text_config.num_attention_heads
            hidden_size = text_config.hidden_size
            head_dim = text_config.head_dim
            num_key_value_heads = text_config.num_key_value_heads
            key_value_dim = head_dim * num_key_value_heads
            query_dim = head_dim * num_attention_heads

        if "q_proj" in new_key and new_key.endswith("weight"):
            tensor = permute_for_rope(tensor, num_attention_heads, query_dim, hidden_size)
        elif "k_proj" in new_key and new_key.endswith("weight"):
            tensor = permute_for_rope(tensor, num_key_value_heads, key_value_dim, hidden_size)

        new_dict[new_key] = tensor
    return new_dict