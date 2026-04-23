def rename_keys(name):
    if "emb" in name:
        name = name.replace("emb", "model.decoder.embed_tokens")
    if "transformer" in name:
        name = name.replace("transformer", "model.decoder")
    if "cross_attention" in name:
        name = name.replace("cross_attention", "encoder_attn")
    if "linear1" in name:
        name = name.replace("linear1", "fc1")
    if "linear2" in name:
        name = name.replace("linear2", "fc2")
    if "norm1" in name:
        name = name.replace("norm1", "self_attn_layer_norm")
    if "norm_cross" in name:
        name = name.replace("norm_cross", "encoder_attn_layer_norm")
    if "norm2" in name:
        name = name.replace("norm2", "final_layer_norm")
    if "out_norm" in name:
        name = name.replace("out_norm", "model.decoder.layer_norm")
    if "linears" in name:
        name = name.replace("linears", "lm_heads")
    if "condition_provider.conditioners.description.output_proj" in name:
        name = name.replace("condition_provider.conditioners.description.output_proj", "enc_to_dec_proj")
    return name