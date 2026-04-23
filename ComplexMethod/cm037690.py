def is_layer_gptq_quantized(
    prefix: str,
    quantized_layers: list[str],
    fused_mapping: Mapping[str, list[str]] = MappingProxyType({}),
) -> bool:
    # prefix: model.layers.0.self_attn.q_proj
    # proj_name: q_proj

    # GPTQ's `modules_in_block_to_quantize`:
    # Substr: ["self_attn.k_proj", "self_attn.v_proj", "self_attn.q_proj"]
    # Full prefix ["model.layers.0.self_attn.q_proj"]

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

        is_quantized = None
        for shard_prefix in shard_prefixes:
            is_shard_quantized = any(
                layer in shard_prefix for layer in quantized_layers
            )

            if is_quantized is None:
                is_quantized = is_shard_quantized
            elif is_shard_quantized != is_quantized:
                raise ValueError(
                    f"Detected some but not all shards of {prefix} "
                    "are quantized. All shards of fused layers "
                    "to have the same precision."
                )
    else:
        is_quantized = any(layer in prefix for layer in quantized_layers)

    assert is_quantized is not None
    return is_quantized