def recursively_load_weights(fairseq_model, hf_model, is_headless):
    unused_weights = []
    fairseq_dict = fairseq_model.state_dict()

    if not is_headless:
        feature_extractor = hf_model.data2vec_audio.feature_extractor
        pos_conv_embedding = hf_model.data2vec_audio.encoder.pos_conv_embed

    else:
        feature_extractor = hf_model.feature_extractor
        pos_conv_embedding = hf_model.encoder.pos_conv_embed

    for name, value in fairseq_dict.items():
        is_used = False
        if "conv_layers" in name:
            load_conv_layer(
                name,
                value,
                feature_extractor,
                unused_weights,
            )
            is_used = True
        elif "pos_conv" in name:
            load_pos_conv_layer(
                name,
                value,
                pos_conv_embedding,
                unused_weights,
            )
            is_used = True
        else:
            for key, mapped_key in MAPPING.items():
                if not is_headless:
                    mapped_key = "data2vec_audio." + mapped_key if mapped_key not in TOP_LEVEL_KEYS else mapped_key
                if key in name or key.split("w2v_model.")[-1] == name.split(".")[0]:
                    is_used = True
                    if "*" in mapped_key:
                        layer_index = name.split(key)[0].split(".")[-2]
                        mapped_key = mapped_key.replace("*", layer_index)
                    if "weight_g" in name:
                        weight_type = "weight_g"
                    elif "weight_v" in name:
                        weight_type = "weight_v"
                    elif "bias" in name:
                        weight_type = "bias"
                    elif "weight" in name:
                        # TODO: don't match quantizer.weight_proj
                        weight_type = "weight"
                    else:
                        weight_type = None
                    set_recursively(hf_model, mapped_key, value, name, weight_type)
                continue
        if not is_used:
            unused_weights.append(name)

    logger.warning(f"Unused weights: {unused_weights}")