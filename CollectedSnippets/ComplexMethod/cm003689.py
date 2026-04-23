def convert_state_dict_to_hf(state_dict):
    new_state_dict = {}
    old_state_dict_keys = set(state_dict.keys())

    # Flattened list of weights to merge. We keep these in the original state dict to merge them later
    original_weights_to_merge = [w for weights in WEIGHTS_TO_MERGE_MAPPING for w in weights[0]]

    # for key, value in state_dict.items():
    for old_key in old_state_dict_keys:
        if old_key.endswith(".inv_freq") or any(w in old_key for w in WEIGHTS_TO_DROP):
            state_dict.pop(old_key)
            continue

        key = old_key
        for key_to_modify, new_key in KEYS_TO_MODIFY_MAPPING.items():
            if key_to_modify in key:
                key = key.replace(key_to_modify, new_key)

        weight = state_dict.pop(old_key)
        if key in original_weights_to_merge:
            new_state_dict[key] = weight
            # Bit of a hack - we need to keep the original weights to merge them later
            state_dict[key] = weight
        else:
            new_state_dict[key] = weight

    return new_state_dict