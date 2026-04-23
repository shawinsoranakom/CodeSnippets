def replace_keys(state_dict):
    model_state_dict = {}
    output_hypernetworks_mlps_pattern = r".*.output_hypernetworks_mlps.(\d+).layers.(\d+).*"
    output_mask_decoder_mlps_pattern = r"mask_decoder.transformer.layers.(\d+).mlp.layers.(\d+).*"
    output_mask_decoder_score_head_pattern = r"mask_decoder.pred_obj_score_head.layers.(\d+).*"
    output_vision_encoder_mlps_pattern = r"vision_encoder.backbone.blocks.(\d+).mlp.layers.(\d+).*"
    output_vision_encoder_neck_pattern = r"vision_encoder.neck.convs.(\d+).conv"
    output_memory_encoder_projection_pattern = r"memory_encoder.o_proj.*"
    memory_attention_pattern = r"memory_attention.*"
    output_object_pointer_proj_pattern = r"object_pointer_proj.layers.(\d+).*"
    output_memory_encoder_mask_downsampler_pattern = r"memory_encoder.mask_downsampler.encoder.(\d+).*"
    perceiver_resampler_patterns = {
        r"spatial_perceiver.latents": r"spatial_perceiver.latents_1d",
        r"spatial_perceiver.latents_1d_2d": r"spatial_perceiver.latents_2d",
        r"spatial_perceiver.layers.(\d+).attn.layer_norm_x": r"spatial_perceiver.layers.\1.layer_norm_input",
        r"spatial_perceiver.layers.(\d+).attn.layer_norm_latents": r"spatial_perceiver.layers.\1.layer_norm_latents",
        r"spatial_perceiver.layers.(\d+).self_attn.layer_norm": r"spatial_perceiver.layers.\1.layer_norm_self",
        r"spatial_perceiver.layers.(\d+).attn.to_q": r"spatial_perceiver.layers.\1.cross_attention.q_proj",
        r"spatial_perceiver.layers.(\d+).attn.to_kv": r"spatial_perceiver.layers.\1.cross_attention.kv_proj_combined",
        r"spatial_perceiver.layers.(\d+).attn.to_out": r"spatial_perceiver.layers.\1.cross_attention.o_proj",
        r"spatial_perceiver.layers.(\d+).self_attn.to_q": r"spatial_perceiver.layers.\1.self_attention.q_proj",
        r"spatial_perceiver.layers.(\d+).self_attn.to_kv": r"spatial_perceiver.layers.\1.self_attention.kv_proj_combined",
        r"spatial_perceiver.layers.(\d+).self_attn.to_out": r"spatial_perceiver.layers.\1.self_attention.o_proj",
        r"spatial_perceiver.layers.(\d+).attn": r"spatial_perceiver.layers.\1.cross_attention",
        r"spatial_perceiver.layers.(\d+).self_attn": r"spatial_perceiver.layers.\1.self_attention",
    }

    for key, value in state_dict.items():
        for key_to_modify, new_key in KEYS_TO_MODIFY_MAPPING.items():
            if key_to_modify in key:
                key = key.replace(key_to_modify, new_key)

        for pattern, replacement in perceiver_resampler_patterns.items():
            if re.match(pattern, key):
                key = re.sub(pattern, replacement, key)

        # vision_encoder.blocks.0.mlp.layers.1.weight -> vision_encoder.blocks.0.mlp.proj_out.weight
        if re.match(output_vision_encoder_mlps_pattern, key):
            layer_nb = int(re.match(output_vision_encoder_mlps_pattern, key).group(2))
            if layer_nb == 0:
                key = key.replace("layers.0", "proj_in")
            elif layer_nb == 1:
                key = key.replace("layers.1", "proj_out")

        if re.match(memory_attention_pattern, key):
            key = key.replace("linear1", "mlp.up_proj")
            key = key.replace("linear2", "mlp.down_proj")

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

        if re.match(output_memory_encoder_mask_downsampler_pattern, key):
            layer_nb = int(re.match(output_memory_encoder_mask_downsampler_pattern, key).group(1))
            if layer_nb == 12:
                key = key.replace(f"encoder.{layer_nb}", "final_conv")
            elif layer_nb % 3 == 0:
                key = key.replace(f"encoder.{layer_nb}", f"layers.{layer_nb // 3}.conv")
            elif layer_nb % 3 == 1:
                key = key.replace(f"encoder.{layer_nb}", f"layers.{layer_nb // 3}.layer_norm")
        if "kv_proj_combined" in key:
            # Split the weight tensor in half along dimension 0 (output dimension)
            k_weight, v_weight = torch.chunk(value, 2, dim=0)
            # Create the k_proj and v_proj keys
            k_key = key.replace("kv_proj_combined", "k_proj")
            v_key = key.replace("kv_proj_combined", "v_proj")
            model_state_dict[k_key] = k_weight
            model_state_dict[v_key] = v_weight
            continue

        model_state_dict[key] = value

    model_state_dict["shared_image_embedding.positional_embedding"] = model_state_dict[
        "prompt_encoder.shared_embedding.positional_embedding"
    ]
    model_state_dict["prompt_encoder.point_embed.weight"] = torch.cat(
        [model_state_dict.pop(f"prompt_encoder.point_embed.{i}.weight") for i in range(4)],
        dim=0,
    )

    return model_state_dict