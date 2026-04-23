def rename_key(key):
    if "visual_encoder" in key:
        key = re.sub("visual_encoder*", "vision_model.encoder", key)
    if "blocks" in key:
        key = re.sub(r"blocks", "layers", key)
    if "attn" in key:
        key = re.sub(r"attn", "self_attn", key)
    if "norm1" in key:
        key = re.sub(r"norm1", "layer_norm1", key)
    if "norm2" in key:
        key = re.sub(r"norm2", "layer_norm2", key)
    if "encoder.norm" in key:
        key = re.sub(r"encoder.norm", "post_layernorm", key)
    if "encoder.patch_embed.proj" in key:
        key = re.sub(r"encoder.patch_embed.proj", "embeddings.patch_embedding", key)

    if "encoder.pos_embed" in key:
        key = re.sub(r"encoder.pos_embed", "embeddings.position_embedding", key)
    if "encoder.cls_token" in key:
        key = re.sub(r"encoder.cls_token", "embeddings.class_embedding", key)

    if "self_attn" in key:
        key = re.sub(r"self_attn.proj", "self_attn.projection", key)

    return key