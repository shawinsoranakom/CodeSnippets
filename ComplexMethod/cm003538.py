def convert_siglip_weight(
    config: SiglipVisionConfig,
    paths: Sequence[str],
    weights: np.ndarray,
) -> tuple[str, np.ndarray]:
    path, prop = paths
    normalized_path: str = ""
    updated_weights: np.ndarray = None

    if path == _SIGLIP_BASE:
        normalized_path = "vision_tower.vision_model.embeddings.position_embedding.weight"
        updated_weights = weights.reshape(-1, config.hidden_size)
    elif path == _SIGLIP_EMBEDDING:
        if prop == "kernel":
            normalized_path = "vision_tower.vision_model.embeddings.patch_embedding.weight"
            updated_weights = weights.transpose(3, 2, 0, 1)
        elif prop == "bias":
            normalized_path = "vision_tower.vision_model.embeddings.patch_embedding.bias"
            updated_weights = weights
        else:
            raise ValueError(f"Unexpected member, `{prop}`, for path `{path}`. Should be `bias` or `kernel`.")
    elif path.startswith(_SIGLIP_TRANSFORMER_ENCODER_BLOCK):
        encoder_block_path = path[_SIGLIP_TRANSFORMER_ENCODER_BLOCK_LEN:]
        next_path_separator_idx = encoder_block_path.find("/")
        layer_idx = encoder_block_path[:next_path_separator_idx]
        encoder_block_path = encoder_block_path[next_path_separator_idx:]
        normalized_path = f"vision_tower.vision_model.encoder.layers.{layer_idx}"

        if encoder_block_path.startswith("/LayerNorm"):
            normalized_path += ".layer_norm1" if path.endswith("_0") else ".layer_norm2"

            if prop == "scale":
                normalized_path += ".weight"
                updated_weights = weights.transpose()
            elif prop == "bias":
                normalized_path += ".bias"
                updated_weights = weights
            else:
                raise ValueError(f"Unexpected member, `{prop}`, for path `{path}`. Should be `bias` or `scale`.")
        elif encoder_block_path.startswith("/MlpBlock_0"):
            normalized_path += ".mlp.fc1" if "/Dense_0" in encoder_block_path else ".mlp.fc2"

            if prop == "kernel":
                normalized_path += ".weight"
                updated_weights = weights.transpose()
            elif prop == "bias":
                normalized_path += ".bias"
                updated_weights = weights
            else:
                raise ValueError(f"Unexpected member, `{prop}`, for path `{path}`. Should be `bias` or `kernel`.")
        elif encoder_block_path.startswith("/MultiHeadDotProductAttention_0"):
            if encoder_block_path.endswith("/key"):
                normalized_path += ".self_attn.k_proj"
            elif encoder_block_path.endswith("/out"):
                normalized_path += ".self_attn.out_proj"
            elif encoder_block_path.endswith("/query"):
                normalized_path += ".self_attn.q_proj"
            elif encoder_block_path.endswith("/value"):
                normalized_path += ".self_attn.v_proj"
            else:
                raise ValueError(f"Unexpected path `{path}` in SigLIP Transformer MultiHeadDotProductAttention_0.")

            if prop == "bias":
                normalized_path += ".bias"
                updated_weights = weights.reshape(-1, config.hidden_size).reshape(-1)
            elif prop == "kernel":
                normalized_path += ".weight"
                updated_weights = weights.reshape(-1, config.hidden_size).transpose()
            else:
                raise ValueError(f"Unexpected member, `{prop}`, for path `{path}`. Should be `bias` or `kernel`.")
        else:
            raise ValueError(f"Unexpected path `{path}` in SigLIP Transformer Encoder Block.")
    elif path == _SIGLIP_TRANSFORMER_ENCODER_NORM:
        if prop == "scale":
            normalized_path = "vision_tower.vision_model.post_layernorm.weight"
            updated_weights = weights.transpose()
        elif prop == "bias":
            normalized_path = "vision_tower.vision_model.post_layernorm.bias"
            updated_weights = weights
        else:
            raise ValueError(f"Unexpected member, `{prop}`, for path `{path}`. Should be `bias` or `scale`.")
    else:
        raise ValueError(f"Unexpected path `{path}`.")

    if "vision" in normalized_path:
        print(normalized_path)
    return normalized_path, updated_weights