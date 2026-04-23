def convert_vision_encoder_weights(
    config,  # Gemma4VisionConfig
    path: str,
    param: str,
    weights: np.ndarray,
) -> Iterable[tuple[str, np.ndarray]]:
    """Convert vision encoder weights from JAX checkpoint to HuggingFace format.

    Args:
        config: Vision config with num_hidden_layers, hidden_size, etc.
        path: Path in the JAX checkpoint (e.g., "VisionEncoder_0/entry/input_projection")
        param: Parameter type (e.g., "w", "scale", "pos_emb")
        weights: NumPy array of weights

    Returns:
        Iterable of (hf_path, converted_weights) tuples
    """
    converted_paths: list[str] = []
    converted_weights: list[Any] = []

    # Patch Embedder - Entry
    # TODO(philculliton): These do not appear to be used currently - they should be loaded by Gemma4VisionPatchEmbedder, by all appearances, but are not currently.
    if path == f"{_VISION_ENCODER_ENTRY}/input_projection":
        if param == "w":
            converted_paths.append("patch_embedder.input_proj.weight")
            # Shape: (768, 768) -> transpose to (768, 768) for nn.Linear
            converted_weights.append(weights.transpose())
    elif path == _VISION_ENCODER_ENTRY:
        if param == "pos_emb":
            converted_paths.append("patch_embedder.position_embedding_table")
            # Shape: (10240, 2, 768) -> transpose to (2, 10240, 768)
            converted_weights.append(weights.transpose(1, 0, 2))

    # Pooler - Exit: convert the learnable scale parameter for vision output scaling
    elif path == _VISION_ENCODER_EXIT:
        if param == "scale":
            converted_paths.append("pooler.scale")
            # JAX shape is (1, 1, d_model), keep as-is for nn.Parameter
            converted_weights.append(weights)

    elif path == _VISION_ENCODER_STANDARDIZE:
        if param == "bias":
            converted_paths.append("std_bias")
            converted_weights.append(weights)
        else:
            converted_paths.append("std_scale")
            converted_weights.append(weights)

    # Transformer Layers (stacked format)
    elif path.startswith(_VISION_ENCODER_TRANSFORMER):
        # All vision transformer layers are stacked in dimension 0
        num_layers = weights.shape[0]
        assert num_layers == config.num_hidden_layers, f"Expected {config.num_hidden_layers} layers, got {num_layers}"

        for i, matrix in enumerate(weights):
            base_path = f"encoder.layers.{i}"

            # Handle clipped einsum states (`ClippedEinsum_0` target paths).
            if path.endswith("attn_vec_einsum/ClippedEinsum_0"):
                converted_paths.append(f"{base_path}.self_attn.o_proj.{param.removeprefix('clip_')}")
                converted_weights.append(matrix)
            if path.endswith("kv_einsum/ClippedEinsum_0"):
                # NOTE: In JAX reference implementations of Gemma, k_proj and v_proj are performed with a single einsum
                # operation. We split this into two operations in Transformers, but they are passed the same input and
                # share the same activation bounds for clipping, thus we re-use the same matrix for both.
                converted_paths.append(f"{base_path}.self_attn.k_proj.{param.removeprefix('clip_')}")
                converted_weights.append(matrix)
                converted_paths.append(f"{base_path}.self_attn.v_proj.{param.removeprefix('clip_')}")
                converted_weights.append(matrix)
            if path.endswith("q_einsum/ClippedEinsum_0"):
                converted_paths.append(f"{base_path}.self_attn.q_proj.{param.removeprefix('clip_')}")
                converted_weights.append(matrix)
            if path.endswith("gating_einsum/ClippedEinsum_0"):
                # NOTE: In JAX reference implementations of Gemma, gate_proj and up_proj are performed with a single
                # einsum operation. We split this into two operations in Transformers, but they are passed the same
                # input and share the same activation bounds for clipping, thus we re-use the same matrix for both.
                converted_paths.append(f"{base_path}.mlp.gate_proj.{param.removeprefix('clip_')}")
                converted_weights.append(matrix)
                converted_paths.append(f"{base_path}.mlp.up_proj.{param.removeprefix('clip_')}")
                converted_weights.append(matrix)
            if path.endswith("linear/ClippedEinsum_0"):
                converted_paths.append(f"{base_path}.mlp.down_proj.{param.removeprefix('clip_')}")
                converted_weights.append(matrix)

            # Handle clipped einsum states (`compression_einsum` target paths).
            # The target path specifies the activation direction (`input` or `output`),
            # and the parameter holds `clip_min` or `clip_max`.
            if "/compression_einsum/" in path:
                direction = path.split("/")[-1].split("_")[0]  # Extracts "input" or "output"
                hf_suffix = f"{direction}_{param.removeprefix('clip_')}"
                einsum_type = path.split("/compression_einsum/")[0].split("/")[-1]

                if einsum_type == "attn_vec_einsum":
                    converted_paths.append(f"{base_path}.self_attn.o_proj.{hf_suffix}")
                    converted_weights.append(matrix)
                elif einsum_type == "kv_einsum":
                    converted_paths.append(f"{base_path}.self_attn.k_proj.{hf_suffix}")
                    converted_weights.append(matrix)
                    converted_paths.append(f"{base_path}.self_attn.v_proj.{hf_suffix}")
                    converted_weights.append(matrix)
                elif einsum_type == "q_einsum":
                    converted_paths.append(f"{base_path}.self_attn.q_proj.{hf_suffix}")
                    converted_weights.append(matrix)
                elif einsum_type == "gating_einsum":
                    converted_paths.append(f"{base_path}.mlp.gate_proj.{hf_suffix}")
                    converted_weights.append(matrix)
                    converted_paths.append(f"{base_path}.mlp.up_proj.{hf_suffix}")
                    converted_weights.append(matrix)
                elif einsum_type == "linear":
                    converted_paths.append(f"{base_path}.mlp.down_proj.{hf_suffix}")
                    converted_weights.append(matrix)

            if path.endswith("attn/attn_vec_einsum"):
                # Shape: (12, 64, 768) -> reshape to (768, 768) for o_proj
                converted_paths.append(f"{base_path}.self_attn.o_proj.linear.weight")
                converted_weights.append(
                    matrix.transpose(2, 0, 1).reshape(config.hidden_size, config.num_attention_heads * config.head_dim)
                )
            elif path.endswith("attn/kv_einsum"):
                # Shape: (2, 12, 768, 64) -> split into k_proj and v_proj
                converted_paths.extend(
                    [
                        f"{base_path}.self_attn.k_proj.linear.weight",
                        f"{base_path}.self_attn.v_proj.linear.weight",
                    ]
                )
                k_proj_weights, v_proj_weights = matrix.transpose(0, 2, 1, 3)
                kv_proj_shape = (config.hidden_size, config.num_key_value_heads * config.head_dim)
                converted_weights.extend(
                    [
                        k_proj_weights.reshape(kv_proj_shape).transpose(),
                        v_proj_weights.reshape(kv_proj_shape).transpose(),
                    ]
                )
            elif path.endswith("attn/q_einsum"):
                # Shape: (12, 768, 64) -> reshape to (768, 768) for q_proj
                converted_paths.append(f"{base_path}.self_attn.q_proj.linear.weight")
                converted_weights.append(
                    matrix.transpose(1, 0, 2)
                    .reshape(config.hidden_size, config.num_attention_heads * config.head_dim)
                    .transpose()
                )
            elif path.endswith("mlp/gating_einsum"):
                # Shape: (2, 3072, 768) -> split into gate_proj and up_proj
                converted_paths.extend(
                    [
                        f"{base_path}.mlp.gate_proj.linear.weight",
                        f"{base_path}.mlp.up_proj.linear.weight",
                    ]
                )
                gate_proj_weight, up_proj_weight = matrix
                converted_weights.extend([gate_proj_weight, up_proj_weight])
            elif path.endswith("mlp/linear"):
                # Shape: (3072, 768) -> transpose for down_proj
                converted_paths.append(f"{base_path}.mlp.down_proj.linear.weight")
                converted_weights.append(matrix.transpose())
            elif path.endswith("post_attention_norm"):
                converted_paths.append(f"{base_path}.post_attention_layernorm.weight")
                converted_weights.append(matrix)
            elif path.endswith("post_ffw_norm"):
                converted_paths.append(f"{base_path}.post_feedforward_layernorm.weight")
                converted_weights.append(matrix)
            elif path.endswith("pre_attention_norm"):
                converted_paths.append(f"{base_path}.input_layernorm.weight")
                converted_weights.append(matrix)
            elif path.endswith("pre_ffw_norm"):
                converted_paths.append(f"{base_path}.pre_feedforward_layernorm.weight")
                converted_weights.append(matrix)
            elif path.endswith("attn/query_norm/scale") or path.endswith("attn/query_norm"):
                # Vision Q/K norms: JAX trained scale values (~-0.6) are not directly
                # usable because the OSS modules expect different shapes and the HF
                # RMSNorm uses scale_shift=1.0 (formula: weight + 1.0).
                # We use zeros to get identity: (0 + 1.0) = 1.0, matching the blaze
                # reference which also uses zeros(head_dim) -> (1+0) = 1.0 identity.
                converted_paths.append(f"{base_path}.self_attn.q_norm.weight")
                converted_weights.append(matrix)
            elif path.endswith("attn/key_norm/scale") or path.endswith("attn/key_norm"):
                converted_paths.append(f"{base_path}.self_attn.k_norm.weight")
                converted_weights.append(matrix)

    if (cpl := len(converted_paths)) != (cwl := len(converted_weights)):
        raise ValueError(
            "The `converted_paths` and `converted_weights` should be the same "
            f"length. Got {cpl} and {cwl}, respectively, for {path}."
        )

    return zip(converted_paths, converted_weights)