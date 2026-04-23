def convert_transformer_weights(
    config: Gemma4TextConfig,
    path: str,
    param: str,
    weights: np.ndarray,
) -> Iterable[tuple[str, np.ndarray]]:
    if path.startswith(_TRANSFORMER_POST_TRAINING_PREFIX):
        path = path[_TRANSFORMER_POST_TRAINING_PREFIX_LEN:]

    converted_paths: list[str] = []
    converted_weights: list[Any] = []
    first_kv_shared_layer_idx = config.num_hidden_layers - getattr(config, "num_kv_shared_layers", 0)

    # Handle new checkpoint format: transformer/layer_N/...
    # TODO(philculliton):Direct handling for unstacked checkpoint type, needs to be merged to allow for unified tensor handling
    if path.startswith(f"{_TRANSFORMER_PARAMETER}/layer_"):
        # Extract layer number from path like "transformer/layer_0/attn/q_einsum"
        layer_str = path.split("/")[1]  # "layer_0"
        layer_idx = int(layer_str.replace("layer_", ""))  # 0
        is_kv_shared_layer = layer_idx >= first_kv_shared_layer_idx > 0
        base_path = f"layers.{layer_idx}"

        # Determine head_dim from actual checkpoint weight dimensions
        # For q_einsum/key_norm, the last dimension tells us the head_dim
        # Otherwise fall back to config
        if path.endswith("attn/key_norm") or path.endswith("attn/query_norm"):
            head_dim = weights.shape[0]  # The norm dimension IS the head_dim
        elif path.endswith("attn/q_einsum"):
            head_dim = weights.shape[-1]  # Last dimension is head_dim
        else:
            # Fall back to config-based determination
            head_dim = (
                config.global_head_dim
                if config.layer_types[layer_idx] == "full_attention" and config.global_head_dim
                else config.head_dim
            )

        # Note: In new format, weights are per-layer (not batched), so no enumerate loop needed
        matrix = weights

        if path.endswith("attn/attn_vec_einsum"):
            converted_paths.append(f"{base_path}.self_attn.o_proj.weight")
            converted_weights.append(
                matrix.transpose(2, 0, 1).reshape(config.hidden_size, config.num_attention_heads * head_dim)
            )
        elif path.endswith("attn/kv_einsum") and not is_kv_shared_layer:
            converted_paths.extend(
                [
                    f"{base_path}.self_attn.k_proj.weight",
                    f"{base_path}.self_attn.v_proj.weight",
                ]
            )
            k_proj_weights, v_proj_weights = matrix.transpose(0, 2, 1, 3)
            kv_proj_shape = (config.hidden_size, config.num_key_value_heads * head_dim)
            converted_weights.extend(
                [
                    k_proj_weights.reshape(kv_proj_shape).transpose(),
                    v_proj_weights.reshape(kv_proj_shape).transpose(),
                ]
            )
        elif path.endswith("attn/k_einsum") and not is_kv_shared_layer:
            converted_paths.append(f"{base_path}.self_attn.k_proj.weight")
            converted_weights.append(
                matrix.transpose(1, 0, 2)
                .reshape(config.hidden_size, config.num_global_key_value_heads * head_dim)
                .transpose()
            )
        elif path.endswith("attn/q_einsum"):
            converted_paths.append(f"{base_path}.self_attn.q_proj.weight")
            converted_weights.append(
                matrix.transpose(1, 0, 2)
                .reshape(config.hidden_size, config.num_attention_heads * head_dim)
                .transpose()
            )
        elif path.endswith("attn/query_norm"):
            converted_paths.append(f"{base_path}.self_attn.q_norm.weight")
            converted_weights.append(matrix)
        elif path.endswith("attn/key_norm") and not is_kv_shared_layer:
            converted_paths.append(f"{base_path}.self_attn.k_norm.weight")
            converted_weights.append(matrix)
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
        elif path.endswith("post_per_layer_input_norm"):
            converted_paths.append(f"{base_path}.post_per_layer_input_norm.weight")
            converted_weights.append(matrix)
        elif path.endswith("pre_attention_norm"):
            converted_paths.append(f"{base_path}.input_layernorm.weight")
            converted_weights.append(matrix)
        elif path.endswith("pre_ffw_norm"):
            converted_paths.append(f"{base_path}.pre_feedforward_layernorm.weight")
            converted_weights.append(matrix)
        elif path.endswith(layer_str) and param == "skip_scale":
            converted_paths.append(f"{base_path}.layer_scalar")
            converted_weights.append(matrix)

    # Handle old checkpoint format: transformer/stacked_layers/attention_type_N/...
    elif path.startswith(_TRANSFORMER_DECODER_BLOCK):
        attention_type_index = int(path[_TRANSFORMER_DECODER_BLOCK_LEN])
        expected_layers_per_group = config.num_hidden_layers / _SLIDING_WINDOW_PATTERN
        observed_layers_per_group = weights.shape[0]
        assert observed_layers_per_group == expected_layers_per_group, (
            f"Expected {observed_layers_per_group=} to be {expected_layers_per_group=}"
        )

        for i, matrix in enumerate(weights):
            layer_idx = _SLIDING_WINDOW_PATTERN * i + attention_type_index
            is_kv_shared_layer = layer_idx >= first_kv_shared_layer_idx > 0
            base_path = f"layers.{layer_idx}"
            head_dim = (
                config.global_head_dim
                if config.layer_types[layer_idx] == "full_attention" and config.global_head_dim
                else config.head_dim
            )

            if param == "skip_scale":
                converted_paths.append(f"{base_path}.layer_scalar")
                converted_weights.append(matrix)
            elif path.endswith("attn/attn_vec_einsum"):
                converted_paths.append(f"{base_path}.self_attn.o_proj.weight")
                converted_weights.append(
                    matrix.transpose(2, 0, 1).reshape(config.hidden_size, config.num_attention_heads * head_dim)
                )
            elif path.endswith("attn/kv_einsum") and not is_kv_shared_layer:
                converted_paths.extend(
                    [
                        f"{base_path}.self_attn.k_proj.weight",
                        f"{base_path}.self_attn.v_proj.weight",
                    ]
                )
                k_proj_weights, v_proj_weights = matrix.transpose(0, 2, 1, 3)
                kv_proj_shape = (config.hidden_size, config.num_key_value_heads * head_dim)
                converted_weights.extend(
                    [
                        k_proj_weights.reshape(kv_proj_shape).transpose(),
                        v_proj_weights.reshape(kv_proj_shape).transpose(),
                    ]
                )
            elif path.endswith("attn/k_einsum") and not is_kv_shared_layer:
                converted_paths.append(f"{base_path}.self_attn.k_proj.weight")
                converted_weights.append(
                    matrix.transpose(1, 0, 2)
                    .reshape(config.hidden_size, config.num_global_key_value_heads * head_dim)
                    .transpose()
                )
            elif path.endswith("attn/q_einsum"):
                converted_paths.append(f"{base_path}.self_attn.q_proj.weight")
                converted_weights.append(
                    matrix.transpose(1, 0, 2)
                    .reshape(config.hidden_size, config.num_attention_heads * head_dim)
                    .transpose()
                )
            elif path.endswith("attn/query_norm"):
                converted_paths.append(f"{base_path}.self_attn.q_norm.weight")
                converted_weights.append(matrix)
            elif path.endswith("attn/key_norm") and not is_kv_shared_layer:
                converted_paths.append(f"{base_path}.self_attn.k_norm.weight")
                converted_weights.append(matrix)
            elif path.endswith("mlp/gating_einsum"):
                # NOTE: The JAX implementations changes the type of the primary `mlp` for MOE models and adds a new
                # `mlp2` that operates _before_ `mlp`. In Hugging Face Transformers we keep the type of `mlp` constant
                # and add an `experts` that operates after `mlp`, so we need to invert this assignment when using MOE arch.
                if config.enable_moe_block:
                    # MoE expert weights: matrix shape [num_experts, 2, moe_intermediate_size, hidden_size]
                    # -> experts.gate_up_proj (nn.Parameter, shape [E, 2*moe_inter, hidden])
                    num_experts, _, expert_inter, hidden_size = matrix.shape
                    gate_up_proj_weight = np.asarray(matrix).reshape(num_experts, 2 * expert_inter, hidden_size)
                    converted_paths.append(f"{base_path}.experts.gate_up_proj")
                    converted_weights.append(gate_up_proj_weight)
                else:
                    # Dense MLP: matrix shape [2, intermediate_size, hidden_size]
                    gate_proj_weight, up_proj_weight = matrix
                    converted_paths.extend([f"{base_path}.mlp.gate_proj.weight", f"{base_path}.mlp.up_proj.weight"])
                    converted_weights.extend([gate_proj_weight, up_proj_weight])
            elif path.endswith("mlp/linear"):
                # NOTE: The JAX implementations changes the type of the primary `mlp` for MOE models and adds a new
                # `mlp2` that operates _before_ `mlp`. In Hugging Face Transformers we keep the type of `mlp` constant
                # and add an `experts` that operates after `mlp`, so we need to invert this assignment when using MOE arch.
                if config.enable_moe_block:
                    # MoE expert down_proj: matrix shape [num_experts, moe_inter, hidden]
                    # -> experts.down_proj (nn.Parameter, shape [E, hidden, moe_inter])
                    converted_paths.append(f"{base_path}.experts.down_proj")
                    converted_weights.append(matrix.transpose(0, 2, 1))
                else:
                    # Dense MLP down_proj
                    converted_paths.append(f"{base_path}.mlp.down_proj.weight")
                    converted_weights.append(matrix.transpose())
            elif path.endswith("mlp/router_logits"):
                # MoE router: matrix shape [hidden_size, num_experts]
                # -> router.proj.weight (nn.Linear, shape [num_experts, hidden_size])
                converted_paths.append(f"{base_path}.router.proj.weight")
                converted_weights.append(matrix.transpose())
            elif param == "router_scale" and path.endswith("mlp"):
                # MoE router scale: shape [hidden_size]
                converted_paths.append(f"{base_path}.router.scale")
                converted_weights.append(matrix)
            elif param == "per_expert_scale" and path.endswith("mlp"):
                # MoE per-expert scale: shape [num_experts]
                converted_paths.append(f"{base_path}.router.per_expert_scale")
                converted_weights.append(matrix)
            elif path.endswith("mlp2/gating_einsum"):
                # Shared expert: matrix shape [2, intermediate_size, hidden_size]
                # -> mlp.gate_proj.weight + mlp.up_proj.weight (nn.Linear)
                converted_paths.extend([f"{base_path}.mlp.gate_proj.weight", f"{base_path}.mlp.up_proj.weight"])
                gate_proj_weight, up_proj_weight = matrix
                converted_weights.extend([gate_proj_weight, up_proj_weight])
            elif path.endswith("mlp2/linear"):
                # Shared expert down_proj: matrix shape [intermediate_size, hidden_size]
                # -> mlp.down_proj.weight (nn.Linear, needs transpose)
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
            elif path.endswith("post_ffw1_norm"):
                converted_paths.append(f"{base_path}.post_feedforward_layernorm_2.weight")
                converted_weights.append(matrix)
            elif path.endswith("post_ffw2_norm"):
                converted_paths.append(f"{base_path}.post_feedforward_layernorm_1.weight")
                converted_weights.append(matrix)
            elif path.endswith("pre_ffw2_norm"):
                converted_paths.append(f"{base_path}.pre_feedforward_layernorm.weight")
                converted_weights.append(matrix)
            elif path.endswith("post_per_layer_input_norm"):
                converted_paths.append(f"{base_path}.post_per_layer_input_norm.weight")
                converted_weights.append(matrix)
            elif path.endswith("pre_attention_norm"):
                converted_paths.append(f"{base_path}.input_layernorm.weight")
                converted_weights.append(matrix)
            elif path.endswith("pre_ffw_norm"):
                # NOTE: The JAX implementations changes the type of the primary `mlp` for MOE models and adds a new
                # `mlp2` that operates _before_ `mlp`. In Hugging Face Transformer we keep the type of `mlp` constant
                # and add an `mlp2` that operates after `mlp`, so we need to invert this assignment when using MOE arch.
                if config.enable_moe_block:
                    # pre_ffw_norm is the pre-norm for ffw1 (MoE); in HF, MoE is mlp_2
                    converted_paths.append(f"{base_path}.pre_feedforward_layernorm_2.weight")
                else:
                    converted_paths.append(f"{base_path}.pre_feedforward_layernorm.weight")
                converted_weights.append(matrix)
    elif path == _TRANSFORMER_EMBEDDER:
        if param == "input_embedding":
            converted_paths.append("embed_tokens.weight")
            converted_weights.append(weights)
        elif param == "per_layer_embeddings":
            converted_paths.append("embed_tokens_per_layer.weight")
            # JAX uses an einsum, but Transformers uses a Linear, so reshapes are required here and in modeling file.
            vocab_size, num_layers, hidden_dim = weights.shape
            converted_weights.append(weights.reshape(vocab_size, num_layers * hidden_dim))
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