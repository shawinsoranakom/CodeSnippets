def recursively_load_weights(fairseq_model, hf_model, is_finetuned):
    unused_weights = []
    fairseq_dict = fairseq_model.state_dict()

    feature_extractor = hf_model.sew.feature_extractor if is_finetuned else hf_model.feature_extractor

    for name, value in fairseq_dict.items():
        is_used = False
        if "conv_layers" in name:
            load_conv_layer(
                name,
                value,
                feature_extractor,
                unused_weights,
                hf_model.config.feat_extract_norm == "group",
            )
            is_used = True
        else:
            for key, mapped_key in MAPPING.items():
                mapped_key = "sew." + mapped_key if (is_finetuned and mapped_key != "lm_head") else mapped_key

                if key in name or key.split("w2v_model.")[-1] == name.split(".")[0]:
                    is_used = True
                    if "*" in mapped_key:
                        layer_index = name.split(key)[0].split(".")[-2]
                        mapped_key = mapped_key.replace("*", layer_index)
                    if "weight_g" in name:
                        weight_type = "weight_g"
                    elif "weight_v" in name:
                        weight_type = "weight_v"
                    elif "weight" in name:
                        weight_type = "weight"
                    elif "bias" in name:
                        weight_type = "bias"
                    else:
                        weight_type = None
                    set_recursively(hf_model, mapped_key, value, name, weight_type)
                continue
        if not is_used:
            unused_weights.append(name)

    logger.warning(f"Unused weights: {unused_weights}")