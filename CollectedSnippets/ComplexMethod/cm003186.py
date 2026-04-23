def recursively_load_weights(orig_dict, hf_model, model_name):
    unused_weights = []

    if model_name in ["encodec_24khz", "encodec_32khz"]:
        MAPPING = MAPPING_24K
    elif model_name == "encodec_48khz":
        MAPPING = MAPPING_48K
    else:
        raise ValueError(f"Unsupported model: {model_name}")

    for name, value in orig_dict.items():
        if should_ignore(name, IGNORE_KEYS):
            logger.info(f"{name} was ignored")
            continue

        is_used = False
        for key, mapped_key in MAPPING.items():
            if "*" in key:
                prefix, suffix = key.split(".*.")
                if prefix in name and suffix in name:
                    key = suffix

            if key in name:
                # HACK otherwise .embed gets initialized with .embed_avg too
                if key.endswith("embed") and name.endswith("embed_avg"):
                    continue

                is_used = True
                if "*" in mapped_key:
                    layer_index = name.split(key)[0].split(".")[-2]
                    mapped_key = mapped_key.replace("*", layer_index)
                if "weight_g" in name:
                    weight_type = "weight_g"
                elif "weight_v" in name:
                    weight_type = "weight_v"
                elif "weight_ih_l0" in name:
                    weight_type = "weight_ih_l0"
                elif "weight_hh_l0" in name:
                    weight_type = "weight_hh_l0"
                elif "bias_ih_l0" in name:
                    weight_type = "bias_ih_l0"
                elif "bias_hh_l0" in name:
                    weight_type = "bias_hh_l0"
                elif "weight_ih_l1" in name:
                    weight_type = "weight_ih_l1"
                elif "weight_hh_l1" in name:
                    weight_type = "weight_hh_l1"
                elif "bias_ih_l1" in name:
                    weight_type = "bias_ih_l1"
                elif "bias_hh_l1" in name:
                    weight_type = "bias_hh_l1"
                elif "bias" in name:
                    weight_type = "bias"
                elif "weight" in name:
                    weight_type = "weight"
                elif "running_mean" in name:
                    weight_type = "running_mean"
                elif "running_var" in name:
                    weight_type = "running_var"
                elif "num_batches_tracked" in name:
                    weight_type = "num_batches_tracked"
                else:
                    weight_type = None
                set_recursively(hf_model, mapped_key, value, name, weight_type)
            continue
        if not is_used:
            unused_weights.append(name)

    logger.warning(f"Unused weights: {unused_weights}")