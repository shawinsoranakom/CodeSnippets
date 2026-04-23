def create_rename_keys(state_dict, config):
    rename_keys = []
    # fmt: off
    ########################################## VISION BACKBONE - START
    # patch embedding layer
    rename_keys.append(("backbone.0.patch_embed.proj.weight",
                        "model.backbone.conv_encoder.model.embeddings.patch_embeddings.projection.weight"))
    rename_keys.append(("backbone.0.patch_embed.proj.bias",
                        "model.backbone.conv_encoder.model.embeddings.patch_embeddings.projection.bias"))
    rename_keys.append(("backbone.0.patch_embed.norm.weight",
                        "model.backbone.conv_encoder.model.embeddings.norm.weight"))
    rename_keys.append(("backbone.0.patch_embed.norm.bias",
                        "model.backbone.conv_encoder.model.embeddings.norm.bias"))

    for layer, depth in enumerate(config.backbone_config.depths):
        for block in range(depth):
            # layernorms
            rename_keys.append((f"backbone.0.layers.{layer}.blocks.{block}.norm1.weight",
                                f"model.backbone.conv_encoder.model.encoder.layers.{layer}.blocks.{block}.layernorm_before.weight"))
            rename_keys.append((f"backbone.0.layers.{layer}.blocks.{block}.norm1.bias",
                                f"model.backbone.conv_encoder.model.encoder.layers.{layer}.blocks.{block}.layernorm_before.bias"))

            rename_keys.append((f"backbone.0.layers.{layer}.blocks.{block}.norm2.weight",
                                f"model.backbone.conv_encoder.model.encoder.layers.{layer}.blocks.{block}.layernorm_after.weight"))
            rename_keys.append((f"backbone.0.layers.{layer}.blocks.{block}.norm2.bias",
                                f"model.backbone.conv_encoder.model.encoder.layers.{layer}.blocks.{block}.layernorm_after.bias"))
            # attention
            rename_keys.append((f"backbone.0.layers.{layer}.blocks.{block}.attn.relative_position_bias_table",
                                f"model.backbone.conv_encoder.model.encoder.layers.{layer}.blocks.{block}.attention.self.relative_position_bias_table"))
            rename_keys.append((f"backbone.0.layers.{layer}.blocks.{block}.attn.proj.weight",
                            f"model.backbone.conv_encoder.model.encoder.layers.{layer}.blocks.{block}.attention.output.dense.weight"))
            rename_keys.append((f"backbone.0.layers.{layer}.blocks.{block}.attn.proj.bias",
                            f"model.backbone.conv_encoder.model.encoder.layers.{layer}.blocks.{block}.attention.output.dense.bias"))
            # intermediate
            rename_keys.append((f"backbone.0.layers.{layer}.blocks.{block}.mlp.fc1.weight",
                            f"model.backbone.conv_encoder.model.encoder.layers.{layer}.blocks.{block}.intermediate.dense.weight"))
            rename_keys.append((f"backbone.0.layers.{layer}.blocks.{block}.mlp.fc1.bias",
                            f"model.backbone.conv_encoder.model.encoder.layers.{layer}.blocks.{block}.intermediate.dense.bias"))

            # output
            rename_keys.append((f"backbone.0.layers.{layer}.blocks.{block}.mlp.fc2.weight",
                            f"model.backbone.conv_encoder.model.encoder.layers.{layer}.blocks.{block}.output.dense.weight"))
            rename_keys.append((f"backbone.0.layers.{layer}.blocks.{block}.mlp.fc2.bias",
                            f"model.backbone.conv_encoder.model.encoder.layers.{layer}.blocks.{block}.output.dense.bias"))

        # downsample
        if layer!=len(config.backbone_config.depths)-1:
            rename_keys.append((f"backbone.0.layers.{layer}.downsample.reduction.weight",
                                f"model.backbone.conv_encoder.model.encoder.layers.{layer}.downsample.reduction.weight"))
            rename_keys.append((f"backbone.0.layers.{layer}.downsample.norm.weight",
                                f"model.backbone.conv_encoder.model.encoder.layers.{layer}.downsample.norm.weight"))
            rename_keys.append((f"backbone.0.layers.{layer}.downsample.norm.bias",
                                f"model.backbone.conv_encoder.model.encoder.layers.{layer}.downsample.norm.bias"))

    for out_indice in config.backbone_config.out_indices:
        # Grounding DINO implementation of out_indices isn't aligned with transformers
        rename_keys.append((f"backbone.0.norm{out_indice-1}.weight",
                        f"model.backbone.conv_encoder.model.hidden_states_norms.stage{out_indice}.weight"))
        rename_keys.append((f"backbone.0.norm{out_indice-1}.bias",
                        f"model.backbone.conv_encoder.model.hidden_states_norms.stage{out_indice}.bias"))

    ########################################## VISION BACKBONE - END

    ########################################## ENCODER - START
    deformable_key_mappings = {
        'self_attn.sampling_offsets.weight': 'deformable_layer.self_attn.sampling_offsets.weight',
        'self_attn.sampling_offsets.bias': 'deformable_layer.self_attn.sampling_offsets.bias',
        'self_attn.attention_weights.weight': 'deformable_layer.self_attn.attention_weights.weight',
        'self_attn.attention_weights.bias': 'deformable_layer.self_attn.attention_weights.bias',
        'self_attn.value_proj.weight': 'deformable_layer.self_attn.value_proj.weight',
        'self_attn.value_proj.bias': 'deformable_layer.self_attn.value_proj.bias',
        'self_attn.output_proj.weight': 'deformable_layer.self_attn.output_proj.weight',
        'self_attn.output_proj.bias': 'deformable_layer.self_attn.output_proj.bias',
        'norm1.weight': 'deformable_layer.self_attn_layer_norm.weight',
        'norm1.bias': 'deformable_layer.self_attn_layer_norm.bias',
        'linear1.weight': 'deformable_layer.fc1.weight',
        'linear1.bias': 'deformable_layer.fc1.bias',
        'linear2.weight': 'deformable_layer.fc2.weight',
        'linear2.bias': 'deformable_layer.fc2.bias',
        'norm2.weight': 'deformable_layer.final_layer_norm.weight',
        'norm2.bias': 'deformable_layer.final_layer_norm.bias',
    }
    text_enhancer_key_mappings = {
        'self_attn.in_proj_weight': 'text_enhancer_layer.self_attn.in_proj_weight',
        'self_attn.in_proj_bias': 'text_enhancer_layer.self_attn.in_proj_bias',
        'self_attn.out_proj.weight': 'text_enhancer_layer.self_attn.out_proj.weight',
        'self_attn.out_proj.bias': 'text_enhancer_layer.self_attn.out_proj.bias',
        'linear1.weight': 'text_enhancer_layer.fc1.weight',
        'linear1.bias': 'text_enhancer_layer.fc1.bias',
        'linear2.weight': 'text_enhancer_layer.fc2.weight',
        'linear2.bias': 'text_enhancer_layer.fc2.bias',
        'norm1.weight': 'text_enhancer_layer.layer_norm_before.weight',
        'norm1.bias': 'text_enhancer_layer.layer_norm_before.bias',
        'norm2.weight': 'text_enhancer_layer.layer_norm_after.weight',
        'norm2.bias': 'text_enhancer_layer.layer_norm_after.bias',
    }
    fusion_key_mappings = {
        'gamma_v': 'fusion_layer.vision_param',
        'gamma_l': 'fusion_layer.text_param',
        'layer_norm_v.weight': 'fusion_layer.layer_norm_vision.weight',
        'layer_norm_v.bias': 'fusion_layer.layer_norm_vision.bias',
        'layer_norm_l.weight': 'fusion_layer.layer_norm_text.weight',
        'layer_norm_l.bias': 'fusion_layer.layer_norm_text.bias',
        'attn.v_proj.weight': 'fusion_layer.attn.vision_proj.weight',
        'attn.v_proj.bias': 'fusion_layer.attn.vision_proj.bias',
        'attn.l_proj.weight': 'fusion_layer.attn.text_proj.weight',
        'attn.l_proj.bias': 'fusion_layer.attn.text_proj.bias',
        'attn.values_v_proj.weight': 'fusion_layer.attn.values_vision_proj.weight',
        'attn.values_v_proj.bias': 'fusion_layer.attn.values_vision_proj.bias',
        'attn.values_l_proj.weight': 'fusion_layer.attn.values_text_proj.weight',
        'attn.values_l_proj.bias': 'fusion_layer.attn.values_text_proj.bias',
        'attn.out_v_proj.weight': 'fusion_layer.attn.out_vision_proj.weight',
        'attn.out_v_proj.bias': 'fusion_layer.attn.out_vision_proj.bias',
        'attn.out_l_proj.weight': 'fusion_layer.attn.out_text_proj.weight',
        'attn.out_l_proj.bias': 'fusion_layer.attn.out_text_proj.bias',
    }
    for layer in range(config.encoder_layers):
        # deformable
        for src, dest in deformable_key_mappings.items():
            rename_keys.append((f"transformer.encoder.layers.{layer}.{src}",
                                f"model.encoder.layers.{layer}.{dest}"))
        # text enhance
        for src, dest in text_enhancer_key_mappings.items():
            rename_keys.append((f"transformer.encoder.text_layers.{layer}.{src}",
                                f"model.encoder.layers.{layer}.{dest}"))
        # fusion layers
        for src, dest in fusion_key_mappings.items():
            rename_keys.append((f"transformer.encoder.fusion_layers.{layer}.{src}",
                                f"model.encoder.layers.{layer}.{dest}"))
    ########################################## ENCODER - END

    ########################################## DECODER - START
    key_mappings_decoder = {
        'cross_attn.sampling_offsets.weight': 'encoder_attn.sampling_offsets.weight',
        'cross_attn.sampling_offsets.bias': 'encoder_attn.sampling_offsets.bias',
        'cross_attn.attention_weights.weight': 'encoder_attn.attention_weights.weight',
        'cross_attn.attention_weights.bias': 'encoder_attn.attention_weights.bias',
        'cross_attn.value_proj.weight': 'encoder_attn.value_proj.weight',
        'cross_attn.value_proj.bias': 'encoder_attn.value_proj.bias',
        'cross_attn.output_proj.weight': 'encoder_attn.output_proj.weight',
        'cross_attn.output_proj.bias': 'encoder_attn.output_proj.bias',
        'norm1.weight': 'encoder_attn_layer_norm.weight',
        'norm1.bias': 'encoder_attn_layer_norm.bias',
        'ca_text.in_proj_weight': 'encoder_attn_text.in_proj_weight',
        'ca_text.in_proj_bias': 'encoder_attn_text.in_proj_bias',
        'ca_text.out_proj.weight': 'encoder_attn_text.out_proj.weight',
        'ca_text.out_proj.bias': 'encoder_attn_text.out_proj.bias',
        'catext_norm.weight': 'encoder_attn_text_layer_norm.weight',
        'catext_norm.bias': 'encoder_attn_text_layer_norm.bias',
        'self_attn.in_proj_weight': 'self_attn.in_proj_weight',
        'self_attn.in_proj_bias': 'self_attn.in_proj_bias',
        'self_attn.out_proj.weight': 'self_attn.out_proj.weight',
        'self_attn.out_proj.bias': 'self_attn.out_proj.bias',
        'norm2.weight': 'self_attn_layer_norm.weight',
        'norm2.bias': 'self_attn_layer_norm.bias',
        'linear1.weight': 'fc1.weight',
        'linear1.bias': 'fc1.bias',
        'linear2.weight': 'fc2.weight',
        'linear2.bias': 'fc2.bias',
        'norm3.weight': 'final_layer_norm.weight',
        'norm3.bias': 'final_layer_norm.bias',
    }
    for layer_num in range(config.decoder_layers):
        source_prefix_decoder = f'transformer.decoder.layers.{layer_num}.'
        target_prefix_decoder = f'model.decoder.layers.{layer_num}.'

        for source_name, target_name in key_mappings_decoder.items():
            rename_keys.append((source_prefix_decoder + source_name,
                               target_prefix_decoder + target_name))
    ########################################## DECODER - END

    ########################################## Additional - START
    for layer_name in state_dict:
        #### TEXT BACKBONE
        if "bert" in layer_name:
            rename_keys.append((layer_name, layer_name.replace("bert", "model.text_backbone")))
        #### INPUT PROJ - PROJECT OUTPUT FEATURES FROM VISION BACKBONE
        if "input_proj" in layer_name:
            rename_keys.append((layer_name, layer_name.replace("input_proj", "model.input_proj_vision")))
        #### INPUT PROJ - PROJECT OUTPUT FEATURES FROM TEXT BACKBONE
        if "feat_map" in layer_name:
            rename_keys.append((layer_name, layer_name.replace("feat_map", "model.text_projection")))
        #### DECODER REFERENCE POINT HEAD
        if "transformer.decoder.ref_point_head" in layer_name:
            rename_keys.append((layer_name, layer_name.replace("transformer.decoder.ref_point_head",
                                                               "model.decoder.reference_points_head")))
        #### DECODER BBOX EMBED
        if "transformer.decoder.bbox_embed" in layer_name:
            rename_keys.append((layer_name, layer_name.replace("transformer.decoder.bbox_embed",
                                                               "model.decoder.bbox_embed")))
        if "transformer.enc_output" in layer_name:
            rename_keys.append((layer_name, layer_name.replace("transformer", "model")))

        if "transformer.enc_out_bbox_embed" in layer_name:
            rename_keys.append((layer_name, layer_name.replace("transformer.enc_out_bbox_embed",
                                                               "model.encoder_output_bbox_embed")))

    rename_keys.append(("transformer.level_embed", "model.level_embed"))
    rename_keys.append(("transformer.decoder.norm.weight", "model.decoder.layer_norm.weight"))
    rename_keys.append(("transformer.decoder.norm.bias", "model.decoder.layer_norm.bias"))
    rename_keys.append(("transformer.tgt_embed.weight", "model.query_position_embeddings.weight"))
    ########################################## Additional - END

    # fmt: on
    return rename_keys