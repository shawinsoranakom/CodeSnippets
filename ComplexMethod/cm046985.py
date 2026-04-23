def _collect_attention_head_dims(config):
    explicit_head_dims = []

    for field_name in (
        "head_dim",
        "global_head_dim",
        "local_head_dim",
        "kv_head_dim",
    ):
        value = _config_get(config, field_name, None)
        if isinstance(value, int) and value > 0:
            explicit_head_dims.append(value)

    if len(explicit_head_dims) != 0:
        return explicit_head_dims

    head_dims = []

    hidden_size_names = ("hidden_size", "d_model", "embed_dim", "dim")
    num_heads_names = ("num_attention_heads", "num_heads", "n_heads")
    for hidden_size_name in hidden_size_names:
        hidden_size = _config_get(config, hidden_size_name, None)
        if not isinstance(hidden_size, int) or hidden_size <= 0:
            continue
        for num_heads_name in num_heads_names:
            num_heads = _config_get(config, num_heads_name, None)
            if (
                isinstance(num_heads, int)
                and num_heads > 0
                and (hidden_size % num_heads) == 0
            ):
                head_dims.append(hidden_size // num_heads)

    return head_dims