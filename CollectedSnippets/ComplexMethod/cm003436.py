def convert_state_dict_sharded(loaded_shards: list[dict], config: MistralConfig):
    """Convert the state dict, when a single `nn.Module` is sharded across different files."""
    new_dict = {}

    num_shards = len(loaded_shards)

    n_heads = config.num_attention_heads
    dim = config.hidden_size
    dims_per_head = dim // n_heads
    num_key_value_heads = config.num_key_value_heads
    n_heads_per_shard = n_heads // num_shards
    num_local_key_value_heads = num_key_value_heads // num_shards
    key_value_dim = dim if n_heads == num_key_value_heads else dims_per_head * num_local_key_value_heads

    original_keys = loaded_shards[0].keys()
    for old_key in original_keys:
        new_key = map_old_key_to_new(old_key)
        cat_dim = get_concat_dim(new_key)

        if "q_proj" in new_key:
            tensor = torch.cat(
                [shard.pop(old_key).view(n_heads_per_shard, dims_per_head, dim) for shard in loaded_shards],
                dim=cat_dim,
            ).reshape(dim, dim)
            tensor = permute_for_rope(tensor, n_heads, dim, dim)
        elif "k_proj" in new_key:
            tensor = torch.cat(
                [shard.pop(old_key).view(num_local_key_value_heads, dims_per_head, dim) for shard in loaded_shards],
                dim=cat_dim,
            ).reshape(key_value_dim, dim)
            tensor = permute_for_rope(tensor, num_key_value_heads, key_value_dim, dim)
        elif "v_proj" in new_key:
            tensor = torch.cat(
                [shard.pop(old_key).view(num_local_key_value_heads, dims_per_head, dim) for shard in loaded_shards],
                dim=cat_dim,
            ).reshape(key_value_dim, dim)
        elif "input_layernorm" in new_key or "post_attention_layernorm" in new_key:
            tensor = loaded_shards[0][old_key].clone()
        elif "model.norm.weight" in new_key:
            tensor = loaded_shards[0][old_key]
        else:
            tensor = torch.cat([shard.pop(old_key) for shard in loaded_shards], dim=cat_dim)

        new_dict[new_key] = tensor

    return new_dict