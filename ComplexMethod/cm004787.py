def rename_keys(state_dict):
    new_state_dict = OrderedDict()
    total_embed_found, patch_emb_offset = 0, 0
    for key, value in state_dict.items():
        if key.startswith("network"):
            key = key.replace("network", "poolformer.encoder")
        if "proj" in key:
            # Works for the first embedding as well as the internal embedding layers
            if key.endswith("bias") and "patch_embed" not in key:
                patch_emb_offset += 1
            to_replace = key[: key.find("proj")]
            key = key.replace(to_replace, f"patch_embeddings.{total_embed_found}.")
            key = key.replace("proj", "projection")
            if key.endswith("bias"):
                total_embed_found += 1
        if "patch_embeddings" in key:
            key = "poolformer.encoder." + key
        if "mlp.fc1" in key:
            key = replace_key_with_offset(key, patch_emb_offset, "mlp.fc1", "output.conv1")
        if "mlp.fc2" in key:
            key = replace_key_with_offset(key, patch_emb_offset, "mlp.fc2", "output.conv2")
        if "norm1" in key:
            key = replace_key_with_offset(key, patch_emb_offset, "norm1", "before_norm")
        if "norm2" in key:
            key = replace_key_with_offset(key, patch_emb_offset, "norm2", "after_norm")
        if "layer_scale_1" in key:
            key = replace_key_with_offset(key, patch_emb_offset, "layer_scale_1", "layer_scale_1")
        if "layer_scale_2" in key:
            key = replace_key_with_offset(key, patch_emb_offset, "layer_scale_2", "layer_scale_2")
        if "head" in key:
            key = key.replace("head", "classifier")
        new_state_dict[key] = value
    return new_state_dict