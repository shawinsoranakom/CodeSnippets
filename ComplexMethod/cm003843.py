def rename_key(name):
    # vision encoder
    if "img_encoder.pos_embed" in name:
        name = name.replace("img_encoder.pos_embed", "vision_model.embeddings.position_embeddings")
    if "img_encoder.patch_embed.proj" in name:
        name = name.replace("img_encoder.patch_embed.proj", "vision_model.embeddings.patch_embeddings.projection")
    if "img_encoder.patch_embed.norm" in name:
        name = name.replace("img_encoder.patch_embed.norm", "vision_model.embeddings.layernorm")
    if "img_encoder.layers" in name:
        name = name.replace("img_encoder.layers", "vision_model.encoder.stages")
    if "blocks" in name and "res" not in name:
        name = name.replace("blocks", "layers")
    if "attn" in name and "pre_assign" not in name:
        name = name.replace("attn", "self_attn")
    if "proj" in name and "self_attn" in name and "text" not in name:
        name = name.replace("proj", "out_proj")
    if "pre_assign_attn.attn.proj" in name:
        name = name.replace("pre_assign_attn.attn.proj", "pre_assign_attn.attn.out_proj")
    if "norm1" in name:
        name = name.replace("norm1", "layer_norm1")
    if "norm2" in name and "pre_assign" not in name:
        name = name.replace("norm2", "layer_norm2")
    if "img_encoder.norm" in name:
        name = name.replace("img_encoder.norm", "vision_model.layernorm")
    # text encoder
    if "text_encoder.token_embedding" in name:
        name = name.replace("text_encoder.token_embedding", "text_model.embeddings.token_embedding")
    if "text_encoder.positional_embedding" in name:
        name = name.replace("text_encoder.positional_embedding", "text_model.embeddings.position_embedding.weight")
    if "text_encoder.transformer.resblocks." in name:
        name = name.replace("text_encoder.transformer.resblocks.", "text_model.encoder.layers.")
    if "ln_1" in name:
        name = name.replace("ln_1", "layer_norm1")
    if "ln_2" in name:
        name = name.replace("ln_2", "layer_norm2")
    if "c_fc" in name:
        name = name.replace("c_fc", "fc1")
    if "c_proj" in name:
        name = name.replace("c_proj", "fc2")
    if "text_encoder" in name:
        name = name.replace("text_encoder", "text_model")
    if "ln_final" in name:
        name = name.replace("ln_final", "final_layer_norm")
    # projection layers
    if "img_projector.linear_hidden." in name:
        name = name.replace("img_projector.linear_hidden.", "visual_projection.")
    if "img_projector.linear_out." in name:
        name = name.replace("img_projector.linear_out.", "visual_projection.3.")
    if "text_projector.linear_hidden" in name:
        name = name.replace("text_projector.linear_hidden", "text_projection")
    if "text_projector.linear_out" in name:
        name = name.replace("text_projector.linear_out", "text_projection.3")

    return name