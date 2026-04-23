def split_qkv(state_dict: dict) -> dict:
    """
    Split combined QKV weights/biases into separate Q, K, V projections.

    Both the vision backbone and text encoder in the original SAM3 use combined QKV projections,
    but the refactored model uses separate Q, K, V projections.

    Args:
        state_dict: State dictionary with combined QKV weights

    Returns:
        State dictionary with split Q, K, V weights
    """
    # Handle vision backbone: .attention.qkv.* → .attention.{q,k,v}_proj.*
    vision_keys_to_split = [key for key in state_dict.keys() if ".attention.qkv." in key]

    for key in vision_keys_to_split:
        qkv = state_dict.pop(key)
        # Split into 3 equal chunks along dimension 0 (output dimension)
        q, k, v = torch.chunk(qkv, 3, dim=0)

        # Create new keys for q_proj, k_proj, v_proj
        state_dict[key.replace(".qkv.", ".q_proj.")] = q
        state_dict[key.replace(".qkv.", ".k_proj.")] = k
        state_dict[key.replace(".qkv.", ".v_proj.")] = v

    # Handle all attention layers with in_proj_* (text encoder, DETR decoder cross-attention, mask decoder)
    # These use: .{attn_type}.in_proj_* → .{attn_type}.{q,k,v}_proj.*
    in_proj_keys_to_split = [key for key in state_dict.keys() if ".in_proj_" in key]

    for key in in_proj_keys_to_split:
        in_proj = state_dict.pop(key)
        # Split into 3 equal chunks along dimension 0 (output dimension)
        q, k, v = torch.chunk(in_proj, 3, dim=0)

        # Create new keys for q_proj, k_proj, v_proj
        # Replace "in_proj_weight" with "q_proj.weight" (or "in_proj_bias" with "q_proj.bias")
        if key.endswith("in_proj_weight"):
            base_key = key.replace("in_proj_weight", "")
            state_dict[base_key + "q_proj.weight"] = q
            state_dict[base_key + "k_proj.weight"] = k
            state_dict[base_key + "v_proj.weight"] = v
        elif key.endswith("in_proj_bias"):
            base_key = key.replace("in_proj_bias", "")
            state_dict[base_key + "q_proj.bias"] = q
            state_dict[base_key + "k_proj.bias"] = k
            state_dict[base_key + "v_proj.bias"] = v

    return state_dict