def rename_key(orig_key):
    if "backbone.0.body" in orig_key:
        orig_key = orig_key.replace("backbone.0.body", "backbone.conv_encoder.model")
    if "transformer" in orig_key:
        orig_key = orig_key.replace("transformer.", "")
    if "norm1" in orig_key:
        if "encoder" in orig_key:
            orig_key = orig_key.replace("norm1", "self_attn_layer_norm")
        else:
            orig_key = orig_key.replace("norm1", "encoder_attn_layer_norm")
    if "norm2" in orig_key:
        if "encoder" in orig_key:
            orig_key = orig_key.replace("norm2", "final_layer_norm")
        else:
            orig_key = orig_key.replace("norm2", "self_attn_layer_norm")
    if "norm3" in orig_key:
        orig_key = orig_key.replace("norm3", "final_layer_norm")
    if "linear1" in orig_key:
        orig_key = orig_key.replace("linear1", "fc1")
    if "linear2" in orig_key:
        orig_key = orig_key.replace("linear2", "fc2")
    if "query_embed" in orig_key:
        orig_key = orig_key.replace("query_embed", "query_position_embeddings")
    if "cross_attn" in orig_key:
        orig_key = orig_key.replace("cross_attn", "encoder_attn")

    return orig_key