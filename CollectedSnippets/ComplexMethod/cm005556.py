def group_layers_by_attn_type(config: PreTrainedConfig) -> tuple[list[list[int]], list[str]]:
    """
    Group layers depending on the attention mix, according to VLLM's hybrid allocator rules:
        - Layers in each group need to have the same type of attention
        - All groups have the same number of layers

    For a model with the following layer types: ["sliding", "full", "full", "sliding", "full", "full", "full", "full"]
    We would get four groups: [0, 3], [1, 2], [4,5] and [6,7].
    """
    # If the config has no layer_type attribute, it means all layers are the same attention type
    layer_types = getattr(config, "layer_types", None)
    if layer_types is None:
        attn_type = "sliding_attention" if getattr(config, "sliding_window", None) is not None else "full_attention"
        layer_types = [attn_type for _ in range(config.num_hidden_layers)]

    # We then count the number of layers of each type
    layer_counts = {}
    for i, layer_type in enumerate(layer_types):
        layer_counts[layer_type] = layer_counts.get(layer_type, []) + [i]

    # The size of all groups is the greatest common divisor of the number of layers of each type
    group_size = gcd(*[len(indices) for indices in layer_counts.values()])

    # We then group the layers by type
    layer_groups = []
    for layer_type, indices in layer_counts.items():
        for i in range(0, len(indices), group_size):
            layer_groups.append(indices[i : i + group_size])
    # And note the layer types
    group_types = [layer_types[lg[0]] for lg in layer_groups]
    return layer_groups, group_types