def convert_backbone_keys(state_dict: dict) -> dict:
    """Convert backbone keys using dinov3_vit conversion functions."""
    backbone_keys = [k for k in state_dict.keys() if k.startswith("backbone.")]
    if not backbone_keys:
        return state_dict

    stripped = {k[len("backbone.") :]: state_dict.pop(k) for k in backbone_keys}
    stripped = split_qkv(stripped)
    key_mapping = convert_old_keys_to_new_keys(list(stripped.keys()))

    result = {}
    for old_key, value in stripped.items():
        new_key = key_mapping.get(old_key, old_key)
        if "bias_mask" in new_key or "k_proj.bias" in new_key or "local_cls_norm" in new_key:
            continue
        if "inv_freq" in new_key:
            continue
        if "mask_token" in new_key and value.dim() == 2:
            value = value.unsqueeze(1)
        result[f"backbone.{new_key}"] = value

    return result