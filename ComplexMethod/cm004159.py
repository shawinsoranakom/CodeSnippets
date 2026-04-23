def rename_key(name, config):
    if "patch_embed.proj" in name and "layers" not in name:
        name = name.replace("patch_embed.proj", "embeddings.patch_embeddings.projection")
    if "patch_embed.norm" in name:
        name = name.replace("patch_embed.norm", "embeddings.patch_embeddings.layernorm")
    if "layers" in name:
        name = name.replace("layers", "encoder.stages")
    if "residual_group.blocks" in name:
        name = name.replace("residual_group.blocks", "layers")
    if "attn.proj" in name:
        name = name.replace("attn.proj", "attention.output.dense")
    if "attn" in name:
        name = name.replace("attn", "attention.self")
    if "norm1" in name:
        name = name.replace("norm1", "layernorm_before")
    if "norm2" in name:
        name = name.replace("norm2", "layernorm_after")
    if "mlp.fc1" in name:
        name = name.replace("mlp.fc1", "intermediate.dense")
    if "mlp.fc2" in name:
        name = name.replace("mlp.fc2", "output.dense")
    if "q_bias" in name:
        name = name.replace("q_bias", "query.bias")
    if "k_bias" in name:
        name = name.replace("k_bias", "key.bias")
    if "v_bias" in name:
        name = name.replace("v_bias", "value.bias")
    if "cpb_mlp" in name:
        name = name.replace("cpb_mlp", "continuous_position_bias_mlp")
    if "patch_embed.proj" in name:
        name = name.replace("patch_embed.proj", "patch_embed.projection")

    if name == "norm.weight":
        name = "layernorm.weight"
    if name == "norm.bias":
        name = "layernorm.bias"

    if "conv_first" in name:
        name = name.replace("conv_first", "first_convolution")

    if (
        "upsample" in name
        or "conv_before_upsample" in name
        or "conv_bicubic" in name
        or "conv_up" in name
        or "conv_hr" in name
        or "conv_last" in name
        or "aux" in name
    ):
        # heads
        if "conv_last" in name:
            name = name.replace("conv_last", "final_convolution")
        if config.upsampler in ["pixelshuffle", "pixelshuffle_aux", "nearest+conv"]:
            if "conv_before_upsample.0" in name:
                name = name.replace("conv_before_upsample.0", "conv_before_upsample")
            if "upsample.0" in name:
                name = name.replace("upsample.0", "upsample.convolution_0")
            if "upsample.2" in name:
                name = name.replace("upsample.2", "upsample.convolution_1")
            name = "upsample." + name
        elif config.upsampler == "pixelshuffledirect":
            name = name.replace("upsample.0.weight", "upsample.conv.weight")
            name = name.replace("upsample.0.bias", "upsample.conv.bias")
        else:
            pass
    else:
        name = "swin2sr." + name

    return name