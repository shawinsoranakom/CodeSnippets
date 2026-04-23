def rename_key(name: str) -> str:
    if "backbone" in name:
        name = name.replace("backbone", "vit")
    if "cls_token" in name:
        name = name.replace("cls_token", "embeddings.cls_token")
    if "det_token" in name:
        name = name.replace("det_token", "embeddings.detection_tokens")
    if "mid_pos_embed" in name:
        name = name.replace("mid_pos_embed", "encoder.mid_position_embeddings")
    if "pos_embed" in name:
        name = name.replace("pos_embed", "embeddings.position_embeddings")
    if "patch_embed.proj" in name:
        name = name.replace("patch_embed.proj", "embeddings.patch_embeddings.projection")
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
    if "class_embed" in name:
        name = name.replace("class_embed", "class_labels_classifier")
    if "bbox_embed" in name:
        name = name.replace("bbox_embed", "bbox_predictor")
    if "vit.norm" in name:
        name = name.replace("vit.norm", "vit.layernorm")

    return name