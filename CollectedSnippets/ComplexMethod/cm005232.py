def convert_state_dict(orig_state_dict, config):
    for key in orig_state_dict.copy():
        val = orig_state_dict.pop(key)

        if "attn.in_proj" in key:
            key_split = key.split(".")
            if key.startswith("visual"):
                layer_num = key_split[3]
                dim = config.vision_config.hidden_size
                if "message_attn" in key:
                    if "weight" in key:
                        orig_state_dict[f"vision_model.encoder.layers.{layer_num}.message_attn.q_proj.weight"] = val[
                            :dim, :
                        ]
                        orig_state_dict[f"vision_model.encoder.layers.{layer_num}.message_attn.k_proj.weight"] = val[
                            dim : dim * 2, :
                        ]
                        orig_state_dict[f"vision_model.encoder.layers.{layer_num}.message_attn.v_proj.weight"] = val[
                            -dim:, :
                        ]
                    else:
                        orig_state_dict[f"vision_model.encoder.layers.{layer_num}.message_attn.q_proj.bias"] = val[
                            :dim
                        ]
                        orig_state_dict[f"vision_model.encoder.layers.{layer_num}.message_attn.k_proj.bias"] = val[
                            dim : dim * 2
                        ]
                        orig_state_dict[f"vision_model.encoder.layers.{layer_num}.message_attn.v_proj.bias"] = val[
                            -dim:
                        ]
                else:
                    if "weight" in key:
                        orig_state_dict[f"vision_model.encoder.layers.{layer_num}.self_attn.q_proj.weight"] = val[
                            :dim, :
                        ]
                        orig_state_dict[f"vision_model.encoder.layers.{layer_num}.self_attn.k_proj.weight"] = val[
                            dim : dim * 2, :
                        ]
                        orig_state_dict[f"vision_model.encoder.layers.{layer_num}.self_attn.v_proj.weight"] = val[
                            -dim:, :
                        ]
                    else:
                        orig_state_dict[f"vision_model.encoder.layers.{layer_num}.self_attn.q_proj.bias"] = val[:dim]
                        orig_state_dict[f"vision_model.encoder.layers.{layer_num}.self_attn.k_proj.bias"] = val[
                            dim : dim * 2
                        ]
                        orig_state_dict[f"vision_model.encoder.layers.{layer_num}.self_attn.v_proj.bias"] = val[-dim:]
            elif key.startswith("mit"):
                layer_num = key_split[2]
                dim = config.vision_config.mit_hidden_size
                if "weight" in key:
                    orig_state_dict[f"mit.encoder.layers.{layer_num}.self_attn.q_proj.weight"] = val[:dim, :]
                    orig_state_dict[f"mit.encoder.layers.{layer_num}.self_attn.k_proj.weight"] = val[dim : dim * 2, :]
                    orig_state_dict[f"mit.encoder.layers.{layer_num}.self_attn.v_proj.weight"] = val[-dim:, :]
                else:
                    orig_state_dict[f"mit.encoder.layers.{layer_num}.self_attn.q_proj.bias"] = val[:dim]
                    orig_state_dict[f"mit.encoder.layers.{layer_num}.self_attn.k_proj.bias"] = val[dim : dim * 2]
                    orig_state_dict[f"mit.encoder.layers.{layer_num}.self_attn.v_proj.bias"] = val[-dim:]
            else:
                layer_num = key_split[2]
                dim = config.text_config.hidden_size
                if "weight" in key:
                    orig_state_dict[f"text_model.encoder.layers.{layer_num}.self_attn.q_proj.weight"] = val[:dim, :]
                    orig_state_dict[f"text_model.encoder.layers.{layer_num}.self_attn.k_proj.weight"] = val[
                        dim : dim * 2, :
                    ]
                    orig_state_dict[f"text_model.encoder.layers.{layer_num}.self_attn.v_proj.weight"] = val[-dim:, :]
                else:
                    orig_state_dict[f"text_model.encoder.layers.{layer_num}.self_attn.q_proj.bias"] = val[:dim]
                    orig_state_dict[f"text_model.encoder.layers.{layer_num}.self_attn.k_proj.bias"] = val[
                        dim : dim * 2
                    ]
                    orig_state_dict[f"text_model.encoder.layers.{layer_num}.self_attn.v_proj.bias"] = val[-dim:]
        else:
            new_key_name = rename_key(key)
            if new_key_name in ["visual_projection.weight", "text_projection.weight"]:
                val = val.T
            orig_state_dict[new_key_name] = val

    return orig_state_dict