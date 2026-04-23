def _convert_model(
    state_dict,
    hf_model,
    convert_list,
    device,
    config,
    unwanted_prefix=None,
):
    hidden_size = config.hidden_size
    head_dim = config.head_dim
    num_heads = int(config.hidden_size // config.head_dim)
    num_key_value_heads = config.num_key_value_heads
    key_value_head_dim = config.num_key_value_heads * head_dim

    # permute for sliced rotary
    def permute(w, n_heads, dim1=hidden_size, dim2=hidden_size):
        return w.view(n_heads, dim1 // n_heads // 2, 2, dim2).transpose(1, 2).reshape(dim1, dim2)

    for k, v in list(state_dict.items()):
        new_k = k if unwanted_prefix is None else k[len(unwanted_prefix) :]
        for old_layer_name, new_layer_name in convert_list:
            if old_layer_name in new_k:
                new_k = new_k.replace(old_layer_name, new_layer_name)

        if "in_proj_weight" in new_k:
            # split qkv into query key and value
            mixed_qkv = state_dict.pop(k)
            qkv_dim = mixed_qkv.size(0) // 3

            query_layer = mixed_qkv[:qkv_dim]
            key_layer = mixed_qkv[qkv_dim : qkv_dim * 2]
            value_layer = mixed_qkv[qkv_dim * 2 :]

            state_dict[new_k.replace("in_proj_weight", "q_proj.weight")] = permute(query_layer, num_heads)
            state_dict[new_k.replace("in_proj_weight", "k_proj.weight")] = permute(
                key_layer, num_key_value_heads, dim1=key_value_head_dim
            )
            state_dict[new_k.replace("in_proj_weight", "v_proj.weight")] = value_layer
        else:
            state_dict[new_k] = state_dict.pop(k)

    extra_keys = set(state_dict.keys()) - set(hf_model.state_dict().keys())
    missing_keys = set(hf_model.state_dict().keys()) - set(state_dict.keys())
    if len(extra_keys) != 0:
        raise ValueError(f"extra keys found: {extra_keys}")
    if len(missing_keys) != 0:
        raise ValueError(f"missing keys: {missing_keys}")
    hf_model.load_state_dict(state_dict, strict=True)
    n_params = param_count(hf_model)

    logger.info(f"model loaded: {round(n_params / 1e6, 1)}M params")

    hf_model.eval()
    hf_model.to(device)
    del state_dict

    return hf_model