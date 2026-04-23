def split_qkv(state_dict: dict) -> dict:
    """Split combined QKV projections into separate Q, K, V projections."""
    # Vision backbone: .attention.qkv.* → .attention.{q,k,v}_proj.*
    for key in [k for k in state_dict if ".attention.qkv." in k]:
        qkv = state_dict.pop(key)
        q, k, v = torch.chunk(qkv, 3, dim=0)
        state_dict[key.replace(".qkv.", ".q_proj.")] = q
        state_dict[key.replace(".qkv.", ".k_proj.")] = k
        state_dict[key.replace(".qkv.", ".v_proj.")] = v

    # Text encoder & attention layers: .in_proj_weight/bias → .{q,k,v}_proj.*
    for key in [k for k in state_dict if ".in_proj_" in k]:
        in_proj = state_dict.pop(key)
        q, k, v = torch.chunk(in_proj, 3, dim=0)
        if key.endswith("in_proj_weight"):
            base = key.replace("in_proj_weight", "")
            state_dict[base + "q_proj.weight"] = q
            state_dict[base + "k_proj.weight"] = k
            state_dict[base + "v_proj.weight"] = v
        elif key.endswith("in_proj_bias"):
            base = key.replace("in_proj_bias", "")
            state_dict[base + "q_proj.bias"] = q
            state_dict[base + "k_proj.bias"] = k
            state_dict[base + "v_proj.bias"] = v

    return state_dict