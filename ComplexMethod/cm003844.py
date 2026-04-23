def convert_state_dict(orig_state_dict, config):
    for key in orig_state_dict.copy():
        val = orig_state_dict.pop(key)

        if "qkv" in key:
            # weights and biases of the key, value and query projections of vision encoder's attention layers require special treatment:
            # we need to split them up into separate matrices/vectors
            key_split = key.split(".")
            stage_num, layer_num = int(key_split[2]), int(key_split[4])
            dim = config.vision_config.hidden_size
            if "weight" in key:
                orig_state_dict[
                    f"vision_model.encoder.stages.{stage_num}.layers.{layer_num}.self_attn.q_proj.weight"
                ] = val[:dim, :]
                orig_state_dict[
                    f"vision_model.encoder.stages.{stage_num}.layers.{layer_num}.self_attn.k_proj.weight"
                ] = val[dim : dim * 2, :]
                orig_state_dict[
                    f"vision_model.encoder.stages.{stage_num}.layers.{layer_num}.self_attn.v_proj.weight"
                ] = val[-dim:, :]
            else:
                orig_state_dict[
                    f"vision_model.encoder.stages.{stage_num}.layers.{layer_num}.self_attn.q_proj.bias"
                ] = val[:dim]
                orig_state_dict[
                    f"vision_model.encoder.stages.{stage_num}.layers.{layer_num}.self_attn.k_proj.bias"
                ] = val[dim : dim * 2]
                orig_state_dict[
                    f"vision_model.encoder.stages.{stage_num}.layers.{layer_num}.self_attn.v_proj.bias"
                ] = val[-dim:]
        elif "in_proj" in key:
            # weights and biases of the key, value and query projections of text encoder's attention layers require special treatment:
            # we need to split them up into separate matrices/vectors
            key_split = key.split(".")
            layer_num = int(key_split[3])
            dim = config.text_config.hidden_size
            if "weight" in key:
                orig_state_dict[f"text_model.encoder.layers.{layer_num}.self_attn.q_proj.weight"] = val[:dim, :]
                orig_state_dict[f"text_model.encoder.layers.{layer_num}.self_attn.k_proj.weight"] = val[
                    dim : dim * 2, :
                ]
                orig_state_dict[f"text_model.encoder.layers.{layer_num}.self_attn.v_proj.weight"] = val[-dim:, :]
            else:
                orig_state_dict[f"text_model.encoder.layers.{layer_num}.self_attn.q_proj.bias"] = val[:dim]
                orig_state_dict[f"text_model.encoder.layers.{layer_num}.self_attn.k_proj.bias"] = val[dim : dim * 2]
                orig_state_dict[f"text_model.encoder.layers.{layer_num}.self_attn.v_proj.bias"] = val[-dim:]
        else:
            new_name = rename_key(key)
            # squeeze if necessary
            if (
                "text_projection.0" in new_name
                or "text_projection.3" in new_name
                or "visual_projection.0" in new_name
                or "visual_projection.3" in new_name
            ):
                orig_state_dict[new_name] = val.squeeze_()
            else:
                orig_state_dict[new_name] = val

    return orig_state_dict