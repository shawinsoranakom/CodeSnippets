def rename_key(name):
    if "encoder.mask_token" in name:
        name = name.replace("encoder.mask_token", "embeddings.mask_token")
    if "encoder.patch_embed.proj" in name:
        name = name.replace("encoder.patch_embed.proj", "embeddings.patch_embeddings.projection")
    if "encoder.patch_embed.norm" in name:
        name = name.replace("encoder.patch_embed.norm", "embeddings.norm")
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

    if name == "encoder.norm.weight":
        name = "layernorm.weight"
    if name == "encoder.norm.bias":
        name = "layernorm.bias"

    if "decoder" in name:
        pass
    else:
        name = "swin." + name

    return name