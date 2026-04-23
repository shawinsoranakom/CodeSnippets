def rename_key(name):
    if "encoder." in name:
        name = name.replace("encoder.", "")
    if "cls_token" in name:
        name = name.replace("cls_token", "timesformer.embeddings.cls_token")
    if "pos_embed" in name:
        name = name.replace("pos_embed", "timesformer.embeddings.position_embeddings")
    if "time_embed" in name:
        name = name.replace("time_embed", "timesformer.embeddings.time_embeddings")
    if "patch_embed.proj" in name:
        name = name.replace("patch_embed.proj", "timesformer.embeddings.patch_embeddings.projection")
    if "patch_embed.norm" in name:
        name = name.replace("patch_embed.norm", "timesformer.embeddings.norm")
    if "blocks" in name:
        name = name.replace("blocks", "timesformer.encoder.layer")
    if "attn.proj" in name:
        name = name.replace("attn.proj", "attention.output.dense")
    if "attn" in name and "bias" not in name and "temporal" not in name:
        name = name.replace("attn", "attention.self")
    if "attn" in name and "temporal" not in name:
        name = name.replace("attn", "attention.attention")
    if "temporal_norm1" in name:
        name = name.replace("temporal_norm1", "temporal_layernorm")
    if "temporal_attn.proj" in name:
        name = name.replace("temporal_attn", "temporal_attention.output.dense")
    if "temporal_fc" in name:
        name = name.replace("temporal_fc", "temporal_dense")
    if "norm1" in name and "temporal" not in name:
        name = name.replace("norm1", "layernorm_before")
    if "norm2" in name:
        name = name.replace("norm2", "layernorm_after")
    if "mlp.fc1" in name:
        name = name.replace("mlp.fc1", "intermediate.dense")
    if "mlp.fc2" in name:
        name = name.replace("mlp.fc2", "output.dense")
    if "norm.weight" in name and "fc" not in name and "temporal" not in name:
        name = name.replace("norm.weight", "timesformer.layernorm.weight")
    if "norm.bias" in name and "fc" not in name and "temporal" not in name:
        name = name.replace("norm.bias", "timesformer.layernorm.bias")
    if "head" in name:
        name = name.replace("head", "classifier")

    return name