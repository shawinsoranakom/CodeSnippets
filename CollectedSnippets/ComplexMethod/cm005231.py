def rename_key(name):
    # text encoder
    if name == "token_embedding.weight":
        name = name.replace("token_embedding.weight", "text_model.embeddings.token_embedding.weight")
    if name == "positional_embedding":
        name = name.replace("positional_embedding", "text_model.embeddings.position_embedding.weight")
    if "ln_1" in name:
        name = name.replace("ln_1", "layer_norm1")
    if "ln_2" in name:
        name = name.replace("ln_2", "layer_norm2")
    if "c_fc" in name:
        name = name.replace("c_fc", "fc1")
    if "c_proj" in name:
        name = name.replace("c_proj", "fc2")
    if name.startswith("transformer.resblocks"):
        name = name.replace("transformer.resblocks", "text_model.encoder.layers")
    if "attn.out_proj" in name and "message" not in name:
        name = name.replace("attn.out_proj", "self_attn.out_proj")
    if "ln_final" in name:
        name = name.replace("ln_final", "text_model.final_layer_norm")
    # visual encoder
    if name == "visual.class_embedding":
        name = name.replace("visual.class_embedding", "vision_model.embeddings.class_embedding")
    if name == "visual.positional_embedding":
        name = name.replace("visual.positional_embedding", "vision_model.embeddings.position_embedding.weight")
    if name.startswith("visual.transformer.resblocks"):
        name = name.replace("visual.transformer.resblocks", "vision_model.encoder.layers")
    if "visual.conv1" in name:
        name = name.replace("visual.conv1", "vision_model.embeddings.patch_embedding")
    if "visual.ln_pre" in name:
        name = name.replace("visual.ln_pre", "vision_model.pre_layernorm")
    if "visual.ln_post" in name:
        name = name.replace("visual.ln_post", "vision_model.post_layernorm")
    if "visual.proj" in name:
        name = name.replace("visual.proj", "visual_projection.weight")
    if "text_projection" in name:
        name = name.replace("text_projection", "text_projection.weight")
    # things on top
    if "prompts_visual_proj" in name:
        name = name.replace("prompts_visual_proj", "prompts_visual_projection")
    if "prompts_visual_ln" in name:
        name = name.replace("prompts_visual_ln", "prompts_visual_layernorm")
    # mit
    if name == "mit.positional_embedding":
        name = name.replace("positional", "position")
    if name.startswith("mit.resblocks"):
        name = name.replace("mit.resblocks", "mit.encoder.layers")
    # prompts generator
    if name.startswith("prompts_generator.norm"):
        name = name.replace("prompts_generator.norm", "prompts_generator.layernorm")

    return name