def convert_dictionary(original_state_dict, vision_config, text_config):
    new_dict = {}

    all_keys = "\n" + "\n".join(original_state_dict.keys())
    old_keys = all_keys
    for old, new in OLD_KEY_TO_NEW_KEY_MAPPING.items():
        all_keys = re.sub(r"\n" + old, r"\n" + new, all_keys)

    OLD_TO_NEW = dict(zip(old_keys.split("\n"), all_keys.split("\n")))

    for key, value in original_state_dict.items():
        new_key = OLD_TO_NEW[key]
        if "vision_encoder" in key:
            _config = vision_config
            num_attention_heads = _config.num_attention_heads
        else:
            _config = text_config
            if "q_proj" in new_key:
                num_attention_heads = _config.num_attention_heads
            if "k_proj" in new_key:
                num_attention_heads = _config.num_key_value_heads

        if "q_proj" in new_key or "k_proj" in new_key:
            value = permute_for_rope(value, num_attention_heads, _config)

        new_dict[new_key] = value
    return new_dict