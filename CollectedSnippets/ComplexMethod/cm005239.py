def rename_key(name):
    # update prefixes
    if "clip_model" in name:
        name = name.replace("clip_model", "clip")
    if "transformer" in name:
        if "visual" in name:
            name = name.replace("visual.transformer", "vision_model")
        else:
            name = name.replace("transformer", "text_model")
    if "resblocks" in name:
        name = name.replace("resblocks", "encoder.layers")
    if "ln_1" in name:
        name = name.replace("ln_1", "layer_norm1")
    if "ln_2" in name:
        name = name.replace("ln_2", "layer_norm2")
    if "c_fc" in name:
        name = name.replace("c_fc", "fc1")
    if "c_proj" in name:
        name = name.replace("c_proj", "fc2")
    if "attn" in name and "self" not in name:
        name = name.replace("attn", "self_attn")
    # text encoder
    if "token_embedding" in name:
        name = name.replace("token_embedding", "text_model.embeddings.token_embedding")
    if "positional_embedding" in name and "visual" not in name:
        name = name.replace("positional_embedding", "text_model.embeddings.position_embedding.weight")
    if "ln_final" in name:
        name = name.replace("ln_final", "text_model.final_layer_norm")
    # vision encoder
    if "visual.class_embedding" in name:
        name = name.replace("visual.class_embedding", "vision_model.embeddings.class_embedding")
    if "visual.conv1" in name:
        name = name.replace("visual.conv1", "vision_model.embeddings.patch_embedding")
    if "visual.positional_embedding" in name:
        name = name.replace("visual.positional_embedding", "vision_model.embeddings.position_embedding.weight")
    if "visual.ln_pre" in name:
        name = name.replace("visual.ln_pre", "vision_model.pre_layrnorm")
    if "visual.ln_post" in name:
        name = name.replace("visual.ln_post", "vision_model.post_layernorm")
    # projection layers
    if "visual.proj" in name:
        name = name.replace("visual.proj", "visual_projection.weight")
    if "text_projection" in name:
        name = name.replace("text_projection", "text_projection.weight")
    # decoder
    if "trans_conv" in name:
        name = name.replace("trans_conv", "transposed_convolution")
    if "film_mul" in name or "film_add" in name or "reduce" in name or "transposed_convolution" in name:
        name = "decoder." + name
    if "blocks" in name:
        name = name.replace("blocks", "decoder.layers")
    if "linear1" in name:
        name = name.replace("linear1", "mlp.fc1")
    if "linear2" in name:
        name = name.replace("linear2", "mlp.fc2")
    if "norm1" in name and "layer_" not in name:
        name = name.replace("norm1", "layer_norm1")
    if "norm2" in name and "layer_" not in name:
        name = name.replace("norm2", "layer_norm2")

    return name