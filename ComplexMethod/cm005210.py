def convert_transformer_weights(
    config: Gemma3nTextConfig,
    path: str,
    param: str,
    weights: np.ndarray,
) -> Iterable[tuple[str, np.ndarray]]:
    if path.startswith(_TRANSFORMER_POST_TRAINING_PREFIX):
        path = path[_TRANSFORMER_POST_TRAINING_PREFIX_LEN:]

    converted_paths: list[str] = []
    converted_weights: list[Any] = []

    if path.startswith(_TRANSFORMER_ALTUP_PROJ):
        index = int(path[-1])
        converted_paths.append(f"altup_projections.{index}.weight")
        converted_weights.append(weights.transpose())
    elif path.startswith(_TRANSFORMER_ALTUP_UNEMB):
        index = int(path[-1])
        converted_paths.append(f"altup_unembed_projections.{index}.weight")
        converted_weights.append(weights.transpose())
    elif path.startswith(_TRANSFORMER_DECODER_BLOCK):
        attention_type_index = int(path[_TRANSFORMER_DECODER_BLOCK_LEN])
        assert weights.shape[0] == config.num_hidden_layers / _SLIDING_WINDOW_PATTERN

        for i, matrix in enumerate(weights):
            layer_idx = _SLIDING_WINDOW_PATTERN * i + attention_type_index
            base_path = f"layers.{layer_idx}"

            if "altup" in path:
                altup_path = f"{base_path}.altup"

                if param == "correct_output_scale":
                    converted_paths.append(f"{altup_path}.correct_output_scale")
                    converted_weights.append(matrix)
                elif param == "correction_coefs":
                    converted_paths.append(f"{altup_path}.correction_coefs.weight")
                    converted_weights.append(matrix.transpose())
                elif param == "prediction_coefs":
                    converted_paths.append(f"{altup_path}.prediction_coefs.weight")
                    converted_weights.append(
                        np.clip(
                            matrix.reshape(config.altup_num_inputs, config.altup_num_inputs**2).transpose(),
                            -config.altup_coef_clip,
                            config.altup_coef_clip,
                        )
                    )

                if path.endswith("modality_router"):
                    converted_paths.append(f"{altup_path}.modality_router.weight")
                    converted_weights.append(matrix.transpose())
                elif path.endswith("router_norm_layer"):
                    converted_paths.append(f"{altup_path}.router_norm.weight")
                    converted_weights.append(matrix)
            elif path.endswith("attn/attn_vec_einsum"):
                converted_paths.append(f"{base_path}.self_attn.o_proj.weight")
                converted_weights.append(
                    matrix.transpose(2, 0, 1).reshape(config.hidden_size, config.num_attention_heads * config.head_dim)
                )
            elif path.endswith("attn/kv_einsum"):
                converted_paths.extend(
                    [
                        f"{base_path}.self_attn.k_proj.weight",
                        f"{base_path}.self_attn.v_proj.weight",
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
                converted_paths.append(f"{base_path}.self_attn.q_proj.weight")
                converted_weights.append(
                    matrix.transpose(1, 0, 2)
                    .reshape(config.hidden_size, config.num_attention_heads * config.head_dim)
                    .transpose()
                )
            elif path.endswith("attn/query_norm"):
                converted_paths.append(f"{base_path}.self_attn.q_norm.weight")
                converted_weights.append(matrix)
            elif path.endswith("attn/key_norm"):
                converted_paths.append(f"{base_path}.self_attn.k_norm.weight")
                converted_weights.append(matrix)
            elif path.endswith("laurel_block/linear_left"):
                converted_paths.append(f"{base_path}.laurel.linear_left.weight")
                converted_weights.append(matrix.transpose())
            elif path.endswith("laurel_block/linear_right"):
                converted_paths.append(f"{base_path}.laurel.linear_right.weight")
                converted_weights.append(matrix.transpose())
            elif path.endswith("mlp/gating_einsum"):
                converted_paths.extend([f"{base_path}.mlp.gate_proj.weight", f"{base_path}.mlp.up_proj.weight"])
                gate_proj_weight, up_proj_weight = matrix
                converted_weights.extend([gate_proj_weight, up_proj_weight])
            elif path.endswith("mlp/linear"):
                converted_paths.append(f"{base_path}.mlp.down_proj.weight")
                converted_weights.append(matrix.transpose())
            elif path.endswith("per_layer_input_gate"):
                converted_paths.append(f"{base_path}.per_layer_input_gate.weight")
                converted_weights.append(matrix.transpose())
            elif path.endswith("per_layer_projection"):
                converted_paths.append(f"{base_path}.per_layer_projection.weight")
                converted_weights.append(matrix.transpose())
            elif path.endswith("post_attention_norm"):
                converted_paths.append(f"{base_path}.post_attention_layernorm.weight")
                converted_weights.append(matrix)
            elif path.endswith("post_ffw_norm"):
                converted_paths.append(f"{base_path}.post_feedforward_layernorm.weight")
                converted_weights.append(matrix)
            elif path.endswith("post_laurel_norm"):
                converted_paths.append(f"{base_path}.laurel.post_laurel_norm.weight")
                converted_weights.append(matrix)
            elif path.endswith("post_per_layer_input_norm"):
                converted_paths.append(f"{base_path}.post_per_layer_input_norm.weight")
                converted_weights.append(matrix)
            elif path.endswith("pre_attention_norm"):
                converted_paths.append(f"{base_path}.input_layernorm.weight")
                converted_weights.append(matrix)
            elif path.endswith("pre_ffw_norm"):
                converted_paths.append(f"{base_path}.pre_feedforward_layernorm.weight")
                converted_weights.append(matrix)
    elif path == _TRANSFORMER_EMBEDDER:
        if param == "input_embedding":
            converted_paths.append("embed_tokens.weight")
            # Gemma 3n model doesn't have soft tokens or "end of" tokens for images and audio in its input and output
            # embeddings, so we resize to avoid bugs observed with Mllama
            pre_expansion_embeddings = weights
            pad_token_slice = slice(config.pad_token_id, config.pad_token_id + 1)
            new_embeddings = np.repeat(pre_expansion_embeddings[pad_token_slice], 256, axis=0)
            weights = np.vstack([pre_expansion_embeddings, new_embeddings])
            converted_weights.append(weights)
        elif param == "per_layer_embeddings":
            converted_paths.append("embed_tokens_per_layer.weight")
            converted_weights.append(
                weights.reshape(
                    config.vocab_size_per_layer_input, config.num_hidden_layers * config.hidden_size_per_layer_input
                )
            )
    elif path.startswith(_TRANSFORMER_EMBEDDER):
        # TODO: ryanmullins - support multimodal norms and projections
        if path.endswith("per_layer_model_projection"):
            converted_paths.append("per_layer_model_projection.weight")
            converted_weights.append(
                weights.reshape(
                    config.hidden_size, config.num_hidden_layers * config.hidden_size_per_layer_input
                ).transpose()
            )
        elif path.endswith("per_layer_projection_norm"):
            converted_paths.append("per_layer_projection_norm.weight")
            converted_weights.append(weights)
    elif path == _TRANSFORMER_FINAL_NORM:
        converted_paths = ["norm.weight"]
        converted_weights = [weights]

    if (cpl := len(converted_paths)) != (cwl := len(converted_weights)):
        raise ValueError(
            "The `converted_paths` and `converted_weights` should be the same "
            f"length. Got {cpl} and {cwl}, respectively, for {path}."
        )

    return zip(converted_paths, converted_weights)