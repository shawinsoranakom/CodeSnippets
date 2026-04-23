def create_rename_keys(config: HieraConfig, base_model: bool, mae_model: bool):
    rename_keys = []
    # fmt: off
    num_stages = len(config.depths)
    # embedding dimensions for input and stages
    dims = [config.embed_dim] + [int(config.embed_dim * config.embed_dim_multiplier**i) for i in range(num_stages)]

    global_layer_idx = 0
    for stage_idx in range(num_stages):
        dim_in = dims[stage_idx]
        dim_out = dims[stage_idx + 1]
        for layer_idx in range(config.depths[stage_idx]):
            rename_keys.append((f"blocks.{global_layer_idx}.norm1.weight", f"hiera.encoder.stages.{stage_idx}.layers.{layer_idx}.layernorm_before.weight"))
            rename_keys.append((f"blocks.{global_layer_idx}.norm1.bias", f"hiera.encoder.stages.{stage_idx}.layers.{layer_idx}.layernorm_before.bias"))
            rename_keys.append((f"blocks.{global_layer_idx}.attn.qkv.weight", f"hiera.encoder.stages.{stage_idx}.layers.{layer_idx}.attn.qkv.weight"))
            rename_keys.append((f"blocks.{global_layer_idx}.attn.qkv.bias", f"hiera.encoder.stages.{stage_idx}.layers.{layer_idx}.attn.qkv.bias"))
            rename_keys.append((f"blocks.{global_layer_idx}.attn.proj.weight", f"hiera.encoder.stages.{stage_idx}.layers.{layer_idx}.attn.proj.weight"))
            rename_keys.append((f"blocks.{global_layer_idx}.attn.proj.bias", f"hiera.encoder.stages.{stage_idx}.layers.{layer_idx}.attn.proj.bias"))
            rename_keys.append((f"blocks.{global_layer_idx}.norm2.weight", f"hiera.encoder.stages.{stage_idx}.layers.{layer_idx}.layernorm_after.weight"))
            rename_keys.append((f"blocks.{global_layer_idx}.norm2.bias", f"hiera.encoder.stages.{stage_idx}.layers.{layer_idx}.layernorm_after.bias"))
            rename_keys.append((f"blocks.{global_layer_idx}.mlp.fc1.weight", f"hiera.encoder.stages.{stage_idx}.layers.{layer_idx}.mlp.fc1.weight"))
            rename_keys.append((f"blocks.{global_layer_idx}.mlp.fc1.bias", f"hiera.encoder.stages.{stage_idx}.layers.{layer_idx}.mlp.fc1.bias"))
            rename_keys.append((f"blocks.{global_layer_idx}.mlp.fc2.weight", f"hiera.encoder.stages.{stage_idx}.layers.{layer_idx}.mlp.fc2.weight"))
            rename_keys.append((f"blocks.{global_layer_idx}.mlp.fc2.bias", f"hiera.encoder.stages.{stage_idx}.layers.{layer_idx}.mlp.fc2.bias"))

            # projection layer only for the first layer of each stage boundary (except the first stage)
            if dim_out != dim_in and layer_idx == 0:
                rename_keys.append((f"blocks.{global_layer_idx}.proj.weight", f"hiera.encoder.stages.{stage_idx}.layers.{layer_idx}.proj.weight"))
                rename_keys.append((f"blocks.{global_layer_idx}.proj.bias", f"hiera.encoder.stages.{stage_idx}.layers.{layer_idx}.proj.bias"))

            global_layer_idx += 1

    # projection layer + position embeddings
    rename_keys.extend(
        [
            ("patch_embed.proj.weight", "hiera.embeddings.patch_embeddings.projection.weight"),
            ("patch_embed.proj.bias", "hiera.embeddings.patch_embeddings.projection.bias")
        ]
    )

    rename_keys.append(("pos_embed", "hiera.embeddings.position_embeddings"))

    if base_model:
        # layernorm + pooler
        rename_keys.extend([("norm.weight", "pooler.layernorm.weight"), ("norm.bias", "pooler.layernorm.bias")])
        # if just the base model, we should remove "hiera" from all keys that start with "hiera"
        rename_keys = [(pair[0], pair[1][6:]) if pair[1].startswith("hiera") else pair for pair in rename_keys]
    elif mae_model:
        rename_keys.extend(
            [
                ("encoder_norm.weight", "encoder_norm.weight"),
                ("encoder_norm.bias", "encoder_norm.bias"),
                ("mask_token", "decoder.mask_token"),
                ("decoder_pos_embed", "decoder.decoder_position_embeddings"),
                ("decoder_norm.weight", "decoder.decoder_norm.weight"),
                ("decoder_norm.bias", "decoder.decoder_norm.bias"),
                ("decoder_pred.weight", "decoder.decoder_pred.weight"),
                ("decoder_pred.bias", "decoder.decoder_pred.bias"),
                ("decoder_embed.weight", "decoder.decoder_embeddings.weight"),
                ("decoder_embed.bias", "decoder.decoder_embeddings.bias")
            ]
        )
        for i in range(config.decoder_depth):
            rename_keys.extend(
                [
                    (f"decoder_blocks.{i}.norm1.weight", f"decoder.decoder_block.layers.{i}.layernorm_before.weight"),
                    (f"decoder_blocks.{i}.norm1.bias", f"decoder.decoder_block.layers.{i}.layernorm_before.bias"),
                    (f"decoder_blocks.{i}.attn.qkv.weight", f"decoder.decoder_block.layers.{i}.attn.qkv.weight"),
                    (f"decoder_blocks.{i}.attn.qkv.bias", f"decoder.decoder_block.layers.{i}.attn.qkv.bias"),
                    (f"decoder_blocks.{i}.attn.proj.weight", f"decoder.decoder_block.layers.{i}.attn.proj.weight"),
                    (f"decoder_blocks.{i}.attn.proj.bias", f"decoder.decoder_block.layers.{i}.attn.proj.bias"),
                    (f"decoder_blocks.{i}.norm2.weight", f"decoder.decoder_block.layers.{i}.layernorm_after.weight"),
                    (f"decoder_blocks.{i}.norm2.bias", f"decoder.decoder_block.layers.{i}.layernorm_after.bias"),
                    (f"decoder_blocks.{i}.mlp.fc1.weight", f"decoder.decoder_block.layers.{i}.mlp.fc1.weight"),
                    (f"decoder_blocks.{i}.mlp.fc1.bias", f"decoder.decoder_block.layers.{i}.mlp.fc1.bias"),
                    (f"decoder_blocks.{i}.mlp.fc2.weight", f"decoder.decoder_block.layers.{i}.mlp.fc2.weight"),
                    (f"decoder_blocks.{i}.mlp.fc2.bias", f"decoder.decoder_block.layers.{i}.mlp.fc2.bias"),
                ]
            )
        for i in range(config.num_query_pool):
            rename_keys.extend(
                [
                    (f"multi_scale_fusion_heads.{i}.weight", f"multiscale_fusion.multi_scale_fusion_heads.{i}.weight"),
                    (f"multi_scale_fusion_heads.{i}.bias", f"multiscale_fusion.multi_scale_fusion_heads.{i}.bias")
                ]
            )
    else:
        # layernorm + classification head
        rename_keys.extend(
            [
                ("norm.weight", "hiera.pooler.layernorm.weight"),
                ("norm.bias", "hiera.pooler.layernorm.bias"),
                ("head.projection.weight", "classifier.weight"),
                ("head.projection.bias", "classifier.bias"),
            ]
        )
    # fmt: on
    return rename_keys