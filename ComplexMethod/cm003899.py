def rename_key(name):
    if "cls_token" in name:
        name = name.replace("cls_token", "vit.embeddings.cls_token")
    if "mask_token" in name:
        name = name.replace("mask_token", "decoder.mask_token")
    if "decoder_pos_embed" in name:
        name = name.replace("decoder_pos_embed", "decoder.decoder_pos_embed")
    if "pos_embed" in name and "decoder" not in name:
        name = name.replace("pos_embed", "vit.embeddings.position_embeddings")
    if "patch_embed.proj" in name:
        name = name.replace("patch_embed.proj", "vit.embeddings.patch_embeddings.projection")
    if "patch_embed.norm" in name:
        name = name.replace("patch_embed.norm", "vit.embeddings.norm")
    if "decoder_blocks" in name:
        name = name.replace("decoder_blocks", "decoder.decoder_layers")
    if "blocks" in name:
        name = name.replace("blocks", "vit.encoder.layer")
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
    if "decoder_embed" in name:
        name = name.replace("decoder_embed", "decoder.decoder_embed")
    if "decoder_norm" in name:
        name = name.replace("decoder_norm", "decoder.decoder_norm")
    if "decoder_pred" in name:
        name = name.replace("decoder_pred", "decoder.decoder_pred")
    if "norm.weight" in name and "decoder" not in name:
        name = name.replace("norm.weight", "vit.layernorm.weight")
    if "norm.bias" in name and "decoder" not in name:
        name = name.replace("norm.bias", "vit.layernorm.bias")

    return name