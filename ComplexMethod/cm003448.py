def rename_key(name):
    if "module.v" in name:
        name = name.replace("module.v", "audio_spectrogram_transformer")
    if "cls_token" in name:
        name = name.replace("cls_token", "embeddings.cls_token")
    if "dist_token" in name:
        name = name.replace("dist_token", "embeddings.distillation_token")
    if "pos_embed" in name:
        name = name.replace("pos_embed", "embeddings.position_embeddings")
    if "patch_embed.proj" in name:
        name = name.replace("patch_embed.proj", "embeddings.patch_embeddings.projection")
    # transformer blocks
    if "blocks" in name:
        name = name.replace("blocks", "encoder.layer")
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
    # final layernorm
    if "audio_spectrogram_transformer.norm" in name:
        name = name.replace("audio_spectrogram_transformer.norm", "audio_spectrogram_transformer.layernorm")
    # classifier head
    if "module.mlp_head.0" in name:
        name = name.replace("module.mlp_head.0", "classifier.layernorm")
    if "module.mlp_head.1" in name:
        name = name.replace("module.mlp_head.1", "classifier.dense")

    return name