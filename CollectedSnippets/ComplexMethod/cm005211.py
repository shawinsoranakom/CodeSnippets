def convert_vision_weights(
    config: Gemma3nVisionConfig,
    path: str,
    param: str,
    weights: np.ndarray,
) -> Iterable[tuple[str, np.ndarray]]:
    def generate_base_path(path: str, block_type: str) -> tuple[str, tuple[int, int]]:
        re_str = rf"{block_type}(\d+)/"
        re_pattern = re.compile(re_str)
        match = re.search(re_pattern, path).group(1)
        idx = abs(int(match)) - 1

        for block_idx, v in enumerate(_MOBILE_NET_TIMM_SUMMED_BLOCK_SIZES):
            if v > idx:
                offset = _MOBILE_NET_TIMM_SUMMED_BLOCK_SIZES[block_idx - 1] if block_idx > 0 else 0
                layer_idx = idx - offset
                return f"blocks.{block_idx}.{layer_idx}", (block_idx, layer_idx)

        raise ValueError(f"could not extract a base path from {path}")

    if _MOBILE_NET_MSFA in path:
        converted_path = "msfa"

        if "ffn/Normalize_0" in path:
            converted_path += ".ffn.pw_exp.bn.weight"
            converted_weight = weights
        elif "ffn/Normalize_1" in path:
            converted_path += ".ffn.pw_proj.bn.weight"
            converted_weight = weights
        elif "ffn/expand" in path:
            converted_path += ".ffn.pw_exp.conv.weight"
            converted_weight = weights.transpose()[:, :, None, None]
        elif "ffn/project" in path:
            converted_path += ".ffn.pw_proj.conv.weight"
            converted_weight = weights.transpose()[:, :, None, None]
        elif "Normalize_0" in path:
            converted_path += ".norm.weight"
            converted_weight = weights
    elif _MOBILE_NET_CONV in path:
        if "Conv_0" in path:
            converted_path = ("conv_stem.conv.weight", "conv_stem.conv.bias")
            converted_weight = weights.transpose(3, 2, 0, 1)
            converted_weight = (converted_weight, np.zeros(converted_weight.shape[0]))
        elif "Normalize_0" in path:
            converted_path = "conv_stem.bn.weight"
            converted_weight = weights
    elif _MOBILE_NET_FIB in path:
        converted_path, _ = generate_base_path(path, _MOBILE_NET_FIB)
        if "Normalize_0" in path:
            converted_path += ".bn1.weight"
            converted_weight = weights
        elif "Normalize_1" in path:
            converted_path += ".bn2.weight"
            converted_weight = weights
        elif "expand_conv" in path:
            converted_path += ".conv_exp.weight"
            converted_weight = weights.transpose(3, 2, 0, 1)
        else:
            converted_path += ".conv_pwl.weight"
            converted_weight = weights.transpose()[:, :, None, None]
    elif _MOBILE_NET_MQA in path:
        converted_path, _ = generate_base_path(path, _MOBILE_NET_MQA)

        if "LayerScale_0" in path:
            converted_path += ".layer_scale.gamma"
            converted_weight = weights
        elif "Normalize_0" in path:
            converted_path += ".norm.weight"
            converted_weight = weights
        elif "Normalize_1" in path:
            converted_path += ".attn.key.norm.weight"
            converted_weight = weights
        elif "Normalize_2" in path:
            converted_path += ".attn.value.norm.weight"
            converted_weight = weights
        elif "key_dwconv" in path:
            converted_path += ".attn.key.down_conv.weight"
            converted_weight = weights.transpose(3, 2, 0, 1)
        elif "key_proj" in path:
            converted_path += ".attn.key.proj.weight"
            converted_weight = weights.transpose()[:, :, None, None]
        elif "output_proj" in path:
            converted_path += ".attn.output.proj.weight"
            converted_weight = weights.transpose()[:, :, None, None]
        elif "query_proj" in path:
            converted_path += ".attn.query.proj.weight"
            converted_weight = weights.transpose()[:, :, None, None]
        elif "value_dwconv" in path:
            converted_path += ".attn.value.down_conv.weight"
            converted_weight = weights.transpose(3, 2, 0, 1)
        elif "value_proj" in path:
            converted_path += ".attn.value.proj.weight"
            converted_weight = weights.transpose()[:, :, None, None]
    elif _MOBILE_NET_UIB in path:
        converted_path, idx_key = generate_base_path(path, _MOBILE_NET_UIB)

        has_dw_start = idx_key in _MOBILE_NET_UIB_HAS_DW_START
        has_dw_mid = idx_key in _MOBILE_NET_UIB_HAS_DW_MID

        if "LayerScale_0" in path:
            converted_path += ".layer_scale.gamma"
            converted_weight = weights
        elif "Normalize_0" in path:
            converted_path += ".dw_start.bn.weight" if has_dw_start else ".pw_exp.bn.weight"
            converted_weight = weights
        elif "Normalize_1" in path:
            converted_path += ".pw_exp.bn.weight" if has_dw_start else ".pw_proj.bn.weight"
            converted_weight = weights
        elif "Normalize_2" in path:
            converted_path += ".dw_mid.bn.weight" if has_dw_mid else ".pw_proj.bn.weight"
            converted_weight = weights
        elif "Normalize_3" in path:
            converted_path += ".pw_proj.bn.weight"
            converted_weight = weights
        elif "expand" in path:
            converted_path += ".pw_exp.conv.weight"
            converted_weight = weights.transpose()[:, :, None, None]
        elif "middle_dwconv" in path:
            converted_path += ".dw_mid.conv.weight"
            converted_weight = weights.transpose(3, 2, 0, 1)
        elif "project" in path:
            converted_path += ".pw_proj.conv.weight"
            converted_weight = weights.transpose()[:, :, None, None]
        elif "start_dwconv" in path:
            converted_path += ".dw_start.conv.weight"
            converted_weight = weights.transpose(3, 2, 0, 1)

    if isinstance(converted_path, (tuple, list)):
        return zip(converted_path, converted_weight)
    else:
        return [(converted_path, converted_weight)]