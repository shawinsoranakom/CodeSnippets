def _match_fused_layer(
    layer_name: str,
    target_layers: Iterable[str],
    fused_mapping: Mapping[str, list[str]],
) -> str | None:
    """
    Match a fused layer name to its corresponding individual layer in
    target_layers. Returns first value in fused_mapping which matches targets

    Implements an "all" matching strategy where a fused layer matches iff
    "all" of its components match

    :param layer_name: layer name
    :param target_layers: list of targets to match the layer against
    :param fused_mapping: map from fused layer names to its components

    Examples:
        layer_name = "model.layers.0.self_attn.qkv_proj"
        target_layers = ["model.layers.0.self_attn.q_proj",
                        "model.layers.0.self_attn.k_proj",
                        "model.layers.0.self_attn.v_proj"]
    """
    # find layer_name in mapping
    fused = next((key for key in fused_mapping if layer_name.endswith(key)), None)
    if fused is None:
        return None

    # expand path of unfused components
    unfused_paths = [
        layer_name.replace(fused, unfused) for unfused in fused_mapping[fused]
    ]

    # for each unfused component, find a match in targets
    unfused_matches: list[str | None] = []
    for unfused in unfused_paths:
        for target in target_layers:
            if _is_equal_or_regex_match(unfused, target):
                unfused_matches.append(target)
                break
        else:
            unfused_matches.append(None)

    return unfused_matches[0] if all(unfused_matches) else None