def convert_predictor_keys(model_state_dict, og_predictor_state_dict, config):
    emb_dim = config.pred_hidden_size
    if "predictor_pos_embed" in og_predictor_state_dict:
        del og_predictor_state_dict["predictor_pos_embed"]
    # update predictor weights
    mask_tokens = {}
    mask_token_keys_to_delete = []
    for key, val in og_predictor_state_dict.copy().items():
        val = og_predictor_state_dict.pop(key)
        key = key.replace("module.backbone.", "")
        if key.startswith("predictor_blocks."):
            key = key.replace("predictor_blocks.", "predictor.layer.")
        if "attn." in key:
            key = key.replace("attn.", "attention.")
        if key == "predictor_pos_embed":
            key = "predictor.embeddings.position_embeddings"
        if "predictor_embed." in key:
            key = key.replace("predictor_embed.", "predictor.embeddings.predictor_embeddings.")
        if "mask_tokens." in key:
            mask_tokens[key.split("mask_tokens.")[-1]] = val
            mask_token_keys_to_delete.append(key)
            # key = key.replace("mask_tokens.", "predictor.embeddings.mask_tokens.")
        if key.startswith("predictor_norm."):
            key = key.replace("predictor_norm.", "predictor.layernorm.")
        if key.startswith("predictor_proj."):
            key = key.replace("predictor_proj.", "predictor.proj.")
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
            og_predictor_state_dict[prefix + "query" + suffix] = q_e
            og_predictor_state_dict[prefix + "key" + suffix] = k_e
            og_predictor_state_dict[prefix + "value" + suffix] = v_e
        else:
            og_predictor_state_dict[key] = val
    mask_tokens = torch.stack([mask_tokens[f"{i}"] for i in range(len(mask_tokens))], dim=0)
    for k in mask_token_keys_to_delete:
        del og_predictor_state_dict[k]
    og_predictor_state_dict["predictor.embeddings.mask_tokens"] = mask_tokens
    return og_predictor_state_dict