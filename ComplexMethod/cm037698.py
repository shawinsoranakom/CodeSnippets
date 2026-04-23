def is_layer_skipped(
    prefix: str,
    ignored_layers: list[str],
    fused_mapping: Mapping[str, list[str]] = MappingProxyType({}),
    *,
    skip_with_substr: bool = False,
) -> bool:
    def prefix_full_match(prefix: str, ignored_layers: list[str]) -> bool:
        return prefix in ignored_layers

    # For case like: ignored_layers = ["self_attn"]
    def substr_match(prefix: str, ignored_layers: list[str]) -> bool:
        return any(layer in prefix for layer in ignored_layers)

    match_func = substr_match if skip_with_substr else prefix_full_match

    # prefix: model.layers.0.self_attn.q_proj
    # proj_name: q_proj
    proj_name = prefix.split(".")[-1]

    # Fused layers like gate_up_proj or qkv_proj will not be fused
    # in the safetensors checkpoint. So, we convert the name
    # from the fused version to unfused + check to make sure that
    # each shard of the fused layer has the same scheme.
    if proj_name in fused_mapping:
        shard_prefixes = [
            prefix.replace(proj_name, shard_proj_name)
            for shard_proj_name in fused_mapping[proj_name]
        ]

        is_skipped = None
        for shard_prefix in shard_prefixes:
            is_shard_skipped = match_func(shard_prefix, ignored_layers)

            if is_skipped is None:
                is_skipped = is_shard_skipped
            elif is_shard_skipped != is_skipped:
                raise ValueError(
                    f"Detected some but not all shards of {prefix} "
                    "are quantized. All shards of fused layers "
                    "to have the same precision."
                )
    elif "experts" in prefix and not skip_with_substr:
        expert_ignore_layers = filter(
            lambda layer_name: "experts" in layer_name, ignored_layers
        )
        return any(
            prefix in layer_name if not skip_with_substr else layer_name in prefix
            for layer_name in expert_ignore_layers
        )
    else:
        is_skipped = match_func(prefix, ignored_layers)

    assert is_skipped is not None
    return is_skipped