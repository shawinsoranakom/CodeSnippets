def convert_state_dict(orig_state_dict, config):
    for key in orig_state_dict.copy():
        val = orig_state_dict.pop(key)

        if key.startswith("clip_model") and "attn.in_proj" in key:
            key_split = key.split(".")
            if "visual" in key:
                layer_num = int(key_split[4])
                dim = config.vision_config.hidden_size
                prefix = "vision_model"
            else:
                layer_num = int(key_split[3])
                dim = config.text_config.hidden_size
                prefix = "text_model"

            if "weight" in key:
                orig_state_dict[f"clip.{prefix}.encoder.layers.{layer_num}.self_attn.q_proj.weight"] = val[:dim, :]
                orig_state_dict[f"clip.{prefix}.encoder.layers.{layer_num}.self_attn.k_proj.weight"] = val[
                    dim : dim * 2, :
                ]
                orig_state_dict[f"clip.{prefix}.encoder.layers.{layer_num}.self_attn.v_proj.weight"] = val[-dim:, :]
            else:
                orig_state_dict[f"clip.{prefix}.encoder.layers.{layer_num}.self_attn.q_proj.bias"] = val[:dim]
                orig_state_dict[f"clip.{prefix}.encoder.layers.{layer_num}.self_attn.k_proj.bias"] = val[dim : dim * 2]
                orig_state_dict[f"clip.{prefix}.encoder.layers.{layer_num}.self_attn.v_proj.bias"] = val[-dim:]
        elif "self_attn" in key and "out_proj" not in key:
            key_split = key.split(".")
            layer_num = int(key_split[1])
            dim = config.reduce_dim
            if "weight" in key:
                orig_state_dict[f"decoder.layers.{layer_num}.self_attn.q_proj.weight"] = val[:dim, :]
                orig_state_dict[f"decoder.layers.{layer_num}.self_attn.k_proj.weight"] = val[dim : dim * 2, :]
                orig_state_dict[f"decoder.layers.{layer_num}.self_attn.v_proj.weight"] = val[-dim:, :]
            else:
                orig_state_dict[f"decoder.layers.{layer_num}.self_attn.q_proj.bias"] = val[:dim]
                orig_state_dict[f"decoder.layers.{layer_num}.self_attn.k_proj.bias"] = val[dim : dim * 2]
                orig_state_dict[f"decoder.layers.{layer_num}.self_attn.v_proj.bias"] = val[-dim:]
        else:
            new_name = rename_key(key)
            if "visual_projection" in new_name or "text_projection" in new_name:
                val = val.T
            orig_state_dict[new_name] = val

    return orig_state_dict