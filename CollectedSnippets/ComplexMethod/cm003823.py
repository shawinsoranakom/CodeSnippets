def recursively_load_weights(fairseq_dict, hf_model):
    unused_weights = []

    for name, value in fairseq_dict.items():
        if should_ignore(name, IGNORE_KEYS):
            logger.info(f"{name} was ignored")
            continue

        is_used = False
        for key, mapped_key in MAPPING.items():
            if key.endswith(".*"):
                key = key[:-1]
            elif "*" in key:
                prefix, suffix = key.split(".*.")
                if prefix in name and suffix in name:
                    key = suffix

            if key in name:
                is_used = True
                if mapped_key.endswith(".*"):
                    layer_index = name.split(key)[-1].split(".")[0]
                    mapped_key = mapped_key.replace("*", layer_index)
                elif "*" in mapped_key:
                    layer_index = name.split(key)[0].split(".")[-2]

                    # remap the layer index since we removed the Flip layers
                    if "flow.flows" in mapped_key:
                        layer_index = str(int(layer_index) // 2)
                    if "duration_predictor.flows" in mapped_key or "duration_predictor.post_flows" in mapped_key:
                        layer_index = str(int(layer_index) // 2 + 1)

                    mapped_key = mapped_key.replace("*", layer_index)
                if "weight_g" in name:
                    weight_type = "weight_g"
                elif "weight_v" in name:
                    weight_type = "weight_v"
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