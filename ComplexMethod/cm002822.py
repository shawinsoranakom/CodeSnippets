def convert_state_dict_to_hf(state_dict):
    new_state_dict = {}

    single_pattern = r"network\.(\d{1,2})"
    double_pattern = r"network\.(\d{1,2})\.(\d{1,2})"
    pos_embedding_pattern = r"stages\.(\d{1,2})\.reparam_conv"

    for key, value in state_dict.items():
        if key.endswith("layer_scale"):
            key = key.replace("layer_scale", "layer_scale.gamma")
        if key.startswith("model.norm"):
            key = key.replace("model.norm", "model.language_model.norm")
        if "token_mixer" not in key:
            key = key.replace(".proj.", ".downsample.proj.")

        matches = re.findall(double_pattern, key)
        if len(matches) == 1:
            match = matches[0]
            key = key.replace(f"network.{match[0]}.{match[1]}", f"stages.{map_to_stage(match[0])}.blocks.{match[1]}")

        matches = re.findall(single_pattern, key)
        if len(matches) == 1:
            match = matches[0]
            key = key.replace(f"network.{match[0]}", f"stages.{map_to_stage(match[0])}")

        matches = re.findall(pos_embedding_pattern, key)
        if len(matches) == 1:
            match = matches[0]
            key = key.replace(f"stages.{match[0]}", f"stages.{match[0]}.pos_emb")

        for key_to_modify, new_key in KEYS_TO_MODIFY_MAPPING.items():
            if key_to_modify in key:
                key = key.replace(key_to_modify, new_key)

        new_state_dict[key] = value
    return new_state_dict