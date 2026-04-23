def _convert_model(
    original_model,
    hf_model,
    convert_list,
):
    state_dict = original_model.state_dict()

    for k, v in list(state_dict.items()):
        new_key = k
        for old_layer_name, new_layer_name in convert_list:
            if old_layer_name in new_key:
                new_key = new_key.replace(old_layer_name, new_layer_name)

        # must do it by hand
        if ".layer_norm" in new_key and new_key.split(".layer_norm")[0][-1].isnumeric():
            new_key = new_key.replace("layer_norm", "final_layer_norm")

        add_key = True
        for key in keys_to_remove:
            if key in new_key:
                state_dict.pop(k)
                add_key = False
                break

        if add_key:
            state_dict[new_key] = state_dict.pop(k)

    extra_keys = set(state_dict.keys()) - set(hf_model.state_dict().keys())
    extra_keys = set({k for k in extra_keys if "num_updates" not in k})  # filter unnecessary param
    missing_keys = set(hf_model.state_dict().keys()) - set(state_dict.keys())
    if len(extra_keys) != 0:
        raise ValueError(f"extra keys found: {extra_keys}")
    if len(missing_keys) != 0:
        raise ValueError(f"missing keys: {missing_keys}")
    hf_model.load_state_dict(state_dict, strict=True)
    n_params = param_count(hf_model)

    logger.info(f"model loaded: {round(n_params / 1e6, 1)}M params")

    hf_model.eval()
    del state_dict

    return hf_model