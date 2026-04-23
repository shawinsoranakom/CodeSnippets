def replace_keys(state_dict):
    model_state_dict = {}
    output_hypernetworks_mlps_pattern = r".*.output_hypernetworks_mlps.(\d+).layers.(\d+).*"
    output_mask_decoder_mlps_pattern = r"mask_decoder.transformer.layers.(\d+).mlp.layers.(\d+).*"
    output_mask_decoder_score_head_pattern = r"mask_decoder.pred_obj_score_head.layers.(\d+).*"
    output_vision_encoder_mlps_pattern = r"vision_encoder.backbone.blocks.(\d+).mlp.layers.(\d+).*"
    output_vision_encoder_neck_pattern = r"vision_encoder.neck.convs.(\d+).conv"
    output_memory_encoder_projection_pattern = r"memory_encoder.o_proj.*"
    output_object_pointer_proj_pattern = r"object_pointer_proj.layers.(\d+).*"
    for key, value in state_dict.items():
        for key_to_modify, new_key in KEYS_TO_MODIFY_MAPPING.items():
            if key_to_modify in key:
                key = key.replace(key_to_modify, new_key)

        # vision_encoder.blocks.0.mlp.layers.1.weight -> vision_encoder.blocks.0.mlp.proj_out.weight
        if re.match(output_vision_encoder_mlps_pattern, key):
            layer_nb = int(re.match(output_vision_encoder_mlps_pattern, key).group(2))
            if layer_nb == 0:
                key = key.replace("layers.0", "proj_in")
            elif layer_nb == 1:
                key = key.replace("layers.1", "proj_out")

        # mask_decoder.transformer.layers.0.mlp.layers.1.weight -> mask_decoder.transformer.layers.1.mlp.proj_out.weight
        if re.match(output_mask_decoder_mlps_pattern, key):
            layer_nb = int(re.match(output_mask_decoder_mlps_pattern, key).group(2))
            if layer_nb == 0:
                key = key.replace("mlp.layers.0", "mlp.proj_in")
            elif layer_nb == 1:
                key = key.replace("mlp.layers.1", "mlp.proj_out")

        # mask_decoder.pred_obj_score_head.layers.1.weight -> mask_decoder.pred_obj_score_head.proj_in.weight
        if re.match(output_mask_decoder_score_head_pattern, key):
            layer_nb = int(re.match(output_mask_decoder_score_head_pattern, key).group(1))
            if layer_nb == 0:
                key = key.replace("layers.0", "proj_in")
            elif layer_nb == 1:
                key = key.replace("layers.1", "layers.0")
            elif layer_nb == 2:
                key = key.replace("layers.2", "proj_out")

        if re.match(output_hypernetworks_mlps_pattern, key):
            layer_nb = int(re.match(output_hypernetworks_mlps_pattern, key).group(2))
            if layer_nb == 0:
                key = key.replace("layers.0", "proj_in")
            elif layer_nb == 1:
                key = key.replace("layers.1", "layers.0")
            elif layer_nb == 2:
                key = key.replace("layers.2", "proj_out")

        # vision_encoder.neck.convs.1.conv.bias -> vision_encoder.neck.convs.1.bias
        if re.match(output_vision_encoder_neck_pattern, key):
            key = key.replace(".conv.", ".")

        # memory_encoder.o_proj.weight -> memory_encoder.projection.weight
        if re.match(output_memory_encoder_projection_pattern, key):
            key = key.replace(".o_proj.", ".projection.")

        if re.match(output_object_pointer_proj_pattern, key):
            layer_nb = int(re.match(output_object_pointer_proj_pattern, key).group(1))
            if layer_nb == 0:
                key = key.replace("layers.0", "proj_in")
            elif layer_nb == 1:
                key = key.replace("layers.1", "layers.0")
            elif layer_nb == 2:
                key = key.replace("layers.2", "proj_out")

                key = key.replace("layers.2", "proj_out")

        model_state_dict[key] = value

    model_state_dict["shared_image_embedding.positional_embedding"] = model_state_dict[
        "prompt_encoder.shared_embedding.positional_embedding"
    ]
    model_state_dict["prompt_encoder.point_embed.weight"] = torch.cat(
        [model_state_dict.pop(f"prompt_encoder.point_embed.{i}.weight") for i in range(4)],
        dim=0,
    )

    return model_state_dict