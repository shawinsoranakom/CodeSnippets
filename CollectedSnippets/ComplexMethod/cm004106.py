def replace_keys(key_mapping: dict):
    output_hypernetworks_mlps_pattern = r".*.output_hypernetworks_mlps.(\d+).layers.(\d+).*"
    output_mask_decoder_mlps_pattern = r"tracker_model.mask_decoder.transformer.layers.(\d+).mlp.layers.(\d+).*"
    output_mask_decoder_score_head_pattern = r"tracker_model.mask_decoder.pred_obj_score_head.layers.(\d+).*"
    output_vision_encoder_mlps_pattern = r"vision_encoder.backbone.blocks.(\d+).mlp.layers.(\d+).*"
    output_vision_encoder_neck_pattern = r"tracker_model.vision_encoder.neck.convs.(\d+).conv"
    output_memory_encoder_projection_pattern = r"tracker_model.memory_encoder.o_proj.*"
    output_object_pointer_proj_pattern = r"tracker_model.object_pointer_proj.layers.(\d+).*"
    output_memory_encoder_mask_downsampler_pattern = r"tracker_model.memory_encoder.mask_downsampler.encoder.(\d+).*"
    key_mapping_copy = key_mapping.copy()
    for value, key in key_mapping_copy.items():
        if not value.startswith("sam2_predictor."):
            continue
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

        if re.match(output_memory_encoder_mask_downsampler_pattern, key):
            layer_nb = int(re.match(output_memory_encoder_mask_downsampler_pattern, key).group(1))
            if layer_nb == 12:
                key = key.replace(f"encoder.{layer_nb}", "final_conv")
            elif layer_nb % 3 == 0:
                key = key.replace(f"encoder.{layer_nb}", f"layers.{layer_nb // 3}.conv")
            elif layer_nb % 3 == 1:
                key = key.replace(f"encoder.{layer_nb}", f"layers.{layer_nb // 3}.layer_norm")
        key_mapping[value] = key

    return key_mapping