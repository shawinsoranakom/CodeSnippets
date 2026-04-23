def _permute_projection_weights(
    tensor, key, num_attention_heads, num_key_value_heads, head_dim, hidden_size, query_dim, key_value_dim
):
    """Permute projection weights for q_proj, k_proj, and v_proj."""
    if "q_proj" in key:
        if "weight" in key:
            tensor = tensor.view(num_attention_heads, head_dim, hidden_size).reshape(query_dim, hidden_size)
            tensor = permute_for_rope(tensor, num_attention_heads, query_dim, hidden_size)
        elif "bias" in key:
            tensor = tensor.view(num_attention_heads, head_dim).reshape(query_dim)
            tensor = permute_for_rope(tensor, num_attention_heads, query_dim)
    elif "k_proj" in key:
        if "weight" in key:
            tensor = tensor.view(num_key_value_heads, head_dim, hidden_size).reshape(key_value_dim, hidden_size)
            tensor = permute_for_rope(tensor, num_key_value_heads, key_value_dim, hidden_size)
        elif "bias" in key:
            tensor = tensor.view(num_key_value_heads, head_dim).reshape(key_value_dim)
            tensor = permute_for_rope(tensor, num_key_value_heads, key_value_dim)
    elif "v_proj" in key:
        if "weight" in key:
            tensor = tensor.view(num_key_value_heads, head_dim, hidden_size).reshape(key_value_dim, hidden_size)
        elif "bias" in key:
            tensor = tensor.view(num_key_value_heads, head_dim).reshape(key_value_dim)

    return tensor