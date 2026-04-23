def create_rename_keys_vision(state_dict, config):
    rename_keys = []
    # fmt: off
    ########################################## VISION BACKBONE - START
    for layer_name in state_dict:
        if layer_name.startswith("backbone") and not layer_name.startswith("backbone.norm"):
            if config.use_timm_backbone:
                layer_name_replace = layer_name.replace("backbone", "vision_backbone.vision_backbone._backbone")
                layer_name_replace = layer_name_replace.replace(".layers.", ".layers_")
                if "downsample" in layer_name:
                    # get layer number
                    layer_num = int(layer_name.split(".")[2])
                    layer_name_replace = layer_name_replace.replace(f"{layer_num}.downsample", f"{layer_num+1}.downsample")
            else:
                layer_name_replace = layer_name.replace("backbone", "vision_backbone.vision_backbone")
                layer_name_replace = layer_name_replace.replace("patch_embed.proj", "embeddings.patch_embeddings.projection")
                layer_name_replace = layer_name_replace.replace("patch_embed.norm", "embeddings.norm")
                if layer_name.startswith("backbone.layers"):
                    layer_name_replace = layer_name_replace.replace("norm1", "layernorm_before")
                    layer_name_replace = layer_name_replace.replace("norm2", "layernorm_after")
                    layer_name_replace = layer_name_replace.replace("attn.proj", "attention.output.dense")
                    layer_name_replace = layer_name_replace.replace("mlp.fc1", "intermediate.dense")
                    layer_name_replace = layer_name_replace.replace("mlp.fc2", "output.dense")
                    layer_name_replace = layer_name_replace.replace(".layers.", ".encoder.layers.")
                    layer_name_replace = layer_name_replace.replace(".attn.", ".attention.self.")
        elif layer_name.startswith("backbone.norm"):
            layer_num = int(layer_name.split("norm")[1].split(".")[0])
            if config.use_timm_backbone:
                layer_name_replace = layer_name.replace("backbone", "vision_backbone")
                layer_name_replace = layer_name_replace.replace(f"norm{layer_num}", f"layer_norms.{layer_num-1}")
            else:
                layer_name_replace = layer_name.replace(f"backbone.norm{layer_num}", f"vision_backbone.vision_backbone.hidden_states_norms.stage{layer_num+1}")
        else:
            continue
        rename_keys.append((layer_name, layer_name_replace))
    ########################################## VISION BACKBONE - END

    ########################################## ENCODER - START
    for layer_name in state_dict:
        if "neck" in layer_name:
            layer_name_replace = layer_name.replace("neck", "encoder")
            layer_name_replace = layer_name_replace.replace("input_proj", "channel_projection_layers")
            if "fpn_blocks" in layer_name or "pan_blocks" in layer_name or "lateral_convs" in layer_name or "downsample_convs" in layer_name:
                layer_name_replace = layer_name_replace.replace(".m.", ".bottlenecks.")
                layer_name_replace = layer_name_replace.replace(".cv", ".conv")
                layer_name_replace = layer_name_replace.replace(".bn", ".norm")
            if "encoder_layer" in layer_name:
                layer_name_replace = layer_name_replace.replace("encoder_layer", "encoder.0.layers.0")
                layer_name_replace = layer_name_replace.replace(".linear", ".fc")
                layer_name_replace = layer_name_replace.replace("norm1", "self_attn_layer_norm")
                layer_name_replace = layer_name_replace.replace("norm2", "final_layer_norm")
            rename_keys.append((layer_name, layer_name_replace))
    ########################################## ENCODER - END

    ########################################## DECODER - START
    for layer_name in state_dict:
        if layer_name.startswith("decoder"):
            layer_name_replace = layer_name.replace("decoder.decoder.layers", "decoder.layers")
            layer_name_replace = layer_name_replace.replace("input_proj", "channel_projection_layers")
            layer_name_replace = layer_name_replace.replace("query_pos_head", "query_position_head")
            layer_name_replace = layer_name_replace.replace("enc_bbox_head", "encoder_bbox_head")
            layer_name_replace = layer_name_replace.replace("enc_output", "encoder_vision_features")
            layer_name_replace = layer_name_replace.replace("dec_score_head", "decoder_class_head")
            layer_name_replace = layer_name_replace.replace("dec_bbox_head", "decoder_bbox_head")
            layer_name_replace = layer_name_replace.replace("enc_score_head", "encoder_class_head")
            rename_keys.append((layer_name, layer_name_replace))
    ########################################## DECODER - END
    # fmt: on
    return rename_keys