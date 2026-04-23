def convert_text_config_to_hf(text_config, original_config):
    # carry directly over
    for key in VALID_TEXT_CONFIG_KEYS:
        text_config[key] = original_config.get(key)

    # special cases
    text_config["hidden_act"] = "silu"  # default value which is not explicit in their json
    text_config["use_cache"] = True  # not always included but we should default to `True`
    text_config["moe_num_experts"] = original_config["moe_num_experts"][0]  # the same for both modalities
    text_config["rope_parameters"] = {
        "rope_type": "default",
        "rope_theta": 500_000.0,
        "mrope_section": [22, 22, 20],
    }
    if text_config["moe_num_shared_experts"] is None:
        text_config["moe_num_shared_experts"] = 0

    # ernie logic to construct mlp/moe layers
    text_config["mlp_layer_types"] = []
    for layer_idx in range(text_config["num_hidden_layers"]):
        if (
            ((layer_idx + 1) % text_config["moe_layer_interval"] == 0)
            and layer_idx >= min(original_config["moe_layer_start_index"])
            and layer_idx <= max(original_config["moe_layer_end_index"])
        ):
            text_config["mlp_layer_types"].append("sparse")
        else:
            text_config["mlp_layer_types"].append("dense")
    text_config.pop("moe_layer_interval", None)

    # delete everything else
    for key in list(text_config.keys()):
        if key not in ALL_TEXT_CONFIG_KEYS:
            del text_config[key]

    return text_config