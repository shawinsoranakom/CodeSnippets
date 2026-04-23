def convert_encoder_keys(model_state_dict, og_encoder_state_dict, config):
    emb_dim = config.hidden_size
    for key, val in og_encoder_state_dict.copy().items():
        val = og_encoder_state_dict.pop(key)
        key = key.replace("module.backbone.", "")
        if key.startswith("blocks."):
            key = key.replace("blocks.", "encoder.layer.")
        if "attn." in key:
            key = key.replace("attn.", "attention.")
        if key == "pos_embed":
            key = "encoder.embeddings.position_embeddings"
        if "patch_embed." in key:
            key = key.replace("patch_embed.", "encoder.embeddings.patch_embeddings.")
        if key.startswith("norm."):
            key = key.replace("norm.", "encoder.layernorm.")
        if "qkv." in key:
            prefix, suffix = key.split("qkv")
            if "bias" in suffix:
                q_e, k_e, v_e = (
                    val[0:emb_dim],
                    val[emb_dim : emb_dim * 2],
                    val[emb_dim * 2 :],
                )
            else:
                q_e, k_e, v_e = (
                    val[0:emb_dim, :],
                    val[emb_dim : emb_dim * 2, :],
                    val[emb_dim * 2 :, :],
                )
            og_encoder_state_dict[prefix + "query" + suffix] = q_e
            og_encoder_state_dict[prefix + "key" + suffix] = k_e
            og_encoder_state_dict[prefix + "value" + suffix] = v_e
        else:
            og_encoder_state_dict[key] = val
    return og_encoder_state_dict