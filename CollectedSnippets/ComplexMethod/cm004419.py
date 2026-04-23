def slice_state_dict(state_dict, config):
    # fmt: off
    # patch embeddings
    state_dict["vision_tower.vision_model.embeddings.patch_embedding.weight"] = state_dict.pop("img/embedding/kernel").transpose(
        3, 2, 0, 1
    )
    state_dict["vision_tower.vision_model.embeddings.patch_embedding.bias"] = state_dict.pop("img/embedding/bias")
    # positional embeddings
    state_dict["vision_tower.vision_model.embeddings.position_embedding.weight"] = state_dict.pop("img/pos_embedding").reshape(
        -1, config.vision_config.hidden_size
    )

    # extract vision layers to be sliced at index 0. There are 27 layers in the base model.
    encoderblock_layernorm0_scale = state_dict.pop("img/Transformer/encoderblock/LayerNorm_0/scale")
    encoderblock_layernorm0_bias = state_dict.pop("img/Transformer/encoderblock/LayerNorm_0/bias")
    encoderblock_layernorm1_scale = state_dict.pop("img/Transformer/encoderblock/LayerNorm_1/scale")
    encoderblock_layernorm1_bias = state_dict.pop("img/Transformer/encoderblock/LayerNorm_1/bias")

    encoderblock_mlp_dense0_kernel= state_dict.pop("img/Transformer/encoderblock/MlpBlock_0/Dense_0/kernel")
    encoderblock_mlp_dense0_bias= state_dict.pop("img/Transformer/encoderblock/MlpBlock_0/Dense_0/bias")
    encoderblock_mlp_dense1_kernel= state_dict.pop("img/Transformer/encoderblock/MlpBlock_0/Dense_1/kernel")
    encoderblock_mlp_dense1_bias= state_dict.pop("img/Transformer/encoderblock/MlpBlock_0/Dense_1/bias")

    encoderblock_attention_0_key_kernel = state_dict.pop("img/Transformer/encoderblock/MultiHeadDotProductAttention_0/key/kernel")
    encoderblock_attention_0_key_bias = state_dict.pop("img/Transformer/encoderblock/MultiHeadDotProductAttention_0/key/bias")
    encoderblock_attention_0_value_kernel = state_dict.pop("img/Transformer/encoderblock/MultiHeadDotProductAttention_0/value/kernel")
    encoderblock_attention_0_value_bias = state_dict.pop("img/Transformer/encoderblock/MultiHeadDotProductAttention_0/value/bias")
    encoderblock_attention_0_query_kernel = state_dict.pop("img/Transformer/encoderblock/MultiHeadDotProductAttention_0/query/kernel")
    encoderblock_attention_0_query_bias = state_dict.pop("img/Transformer/encoderblock/MultiHeadDotProductAttention_0/query/bias")
    encoderblock_attention_0_out_kernel = state_dict.pop("img/Transformer/encoderblock/MultiHeadDotProductAttention_0/out/kernel")
    encoderblock_attention_0_out_bias = state_dict.pop("img/Transformer/encoderblock/MultiHeadDotProductAttention_0/out/bias")

    for i in range(config.vision_config.num_hidden_layers):
        state_dict[f"vision_tower.vision_model.encoder.layers.{i}.layer_norm1.weight"] = encoderblock_layernorm0_scale[i].transpose()
        state_dict[f"vision_tower.vision_model.encoder.layers.{i}.layer_norm1.bias"] = encoderblock_layernorm0_bias[i]
        state_dict[f"vision_tower.vision_model.encoder.layers.{i}.layer_norm2.weight"] = encoderblock_layernorm1_scale[i].transpose()
        state_dict[f"vision_tower.vision_model.encoder.layers.{i}.layer_norm2.bias"] = encoderblock_layernorm1_bias[i]

        state_dict[f"vision_tower.vision_model.encoder.layers.{i}.mlp.fc1.weight"] = encoderblock_mlp_dense0_kernel[i].transpose()
        state_dict[f"vision_tower.vision_model.encoder.layers.{i}.mlp.fc1.bias"] = encoderblock_mlp_dense0_bias[i]
        state_dict[f"vision_tower.vision_model.encoder.layers.{i}.mlp.fc2.weight"] = encoderblock_mlp_dense1_kernel[i].transpose()
        state_dict[f"vision_tower.vision_model.encoder.layers.{i}.mlp.fc2.bias"] = encoderblock_mlp_dense1_bias[i]
        state_dict[f"vision_tower.vision_model.encoder.layers.{i}.self_attn.k_proj.weight"] = encoderblock_attention_0_key_kernel[i].reshape(-1, config.vision_config.hidden_size).transpose()
        state_dict[f"vision_tower.vision_model.encoder.layers.{i}.self_attn.k_proj.bias"] = encoderblock_attention_0_key_bias[i].reshape(-1, config.vision_config.hidden_size).reshape(-1)
        state_dict[f"vision_tower.vision_model.encoder.layers.{i}.self_attn.v_proj.weight"] = encoderblock_attention_0_value_kernel[i].reshape(-1, config.vision_config.hidden_size).transpose()
        state_dict[f"vision_tower.vision_model.encoder.layers.{i}.self_attn.v_proj.bias"] = encoderblock_attention_0_value_bias[i].reshape(-1, config.vision_config.hidden_size).reshape(-1)
        state_dict[f"vision_tower.vision_model.encoder.layers.{i}.self_attn.q_proj.weight"] = encoderblock_attention_0_query_kernel[i].reshape(-1, config.vision_config.hidden_size).transpose()
        state_dict[f"vision_tower.vision_model.encoder.layers.{i}.self_attn.q_proj.bias"] = encoderblock_attention_0_query_bias[i].reshape(-1, config.vision_config.hidden_size).reshape(-1)
        state_dict[f"vision_tower.vision_model.encoder.layers.{i}.self_attn.out_proj.weight"] = encoderblock_attention_0_out_kernel[i].reshape(-1, config.vision_config.hidden_size).transpose()
        state_dict[f"vision_tower.vision_model.encoder.layers.{i}.self_attn.out_proj.bias"] = encoderblock_attention_0_out_bias[i].reshape(-1, config.vision_config.hidden_size).reshape(-1)

    state_dict["vision_tower.vision_model.post_layernorm.weight"] = state_dict.pop("img/Transformer/encoder_norm/scale").transpose()
    state_dict["vision_tower.vision_model.post_layernorm.bias"] = state_dict.pop("img/Transformer/encoder_norm/bias")

    # multimodal projector

    state_dict['multi_modal_projector.linear.weight'] = state_dict.pop("img/head/kernel").transpose()
    state_dict['multi_modal_projector.linear.bias'] = state_dict.pop("img/head/bias")

    # text decoder (gemma)

    embedding_vector = state_dict.pop("llm/embedder/input_embedding")
    state_dict["language_model.model.embed_tokens.weight"] = embedding_vector

    # pop the einsum attention + mlp representations. There are 26 layers in gemma2-2b.

    llm_attention_attn_vec_einsum = state_dict.pop("llm/layers/attn/attn_vec_einsum/w")
    #  (26, 2, 4, 2304, 256) for 2b-224, 4 kv heads and 26 layers
    llm_attention_kv_einsum = state_dict.pop("llm/layers/attn/kv_einsum/w")
    llm_attention_q_einsum = state_dict.pop("llm/layers/attn/q_einsum/w")
    llm_mlp_gating_einsum = state_dict.pop("llm/layers/mlp/gating_einsum")
    llm_mlp_linear = state_dict.pop("llm/layers/mlp/linear")
    # TODO verify correctness of layer norm loading
    llm_input_layernorm = state_dict.pop("llm/layers/pre_attention_norm/scale")
    llm_pre_feedforward_layernorm = state_dict.pop("llm/layers/pre_ffw_norm/scale")

    llm_post_attention_layernorm = state_dict.pop("llm/layers/post_attention_norm/scale")
    llm_post_feedforward_layernorm = state_dict.pop("llm/layers/post_ffw_norm/scale")

    for i in range(config.text_config.num_hidden_layers):
        # llm_attention_q_einsum[i].shape = (8, 2048, 256)
        # q_proj_weight_reshaped = llm_attention_q_einsum[i].transpose(0, 2, 1).reshape(config.text_config.num_attention_heads * config.text_config.head_dim, config.text_config.hidden_size)

        """
        q shape (8, 2304, 256)
        k shape (4, 2304, 256)
        v shape (4, 2304, 256)
        o shape (8, 256, 2304)

        """
        q_transpose = (0, 2, 1)
        k_transpose = (0, 2, 1)
        v_transpose = (0, 2, 1)
        o_transpose = (2, 0, 1)

        q_weight_matrices = llm_attention_q_einsum[i].transpose(*q_transpose)
        q_proj_weight_reshaped = q_weight_matrices
        q_proj_weight_reshaped = q_proj_weight_reshaped.reshape(config.text_config.num_attention_heads * config.text_config.head_dim, config.text_config.hidden_size)
        state_dict[f"language_model.model.layers.{i}.self_attn.q_proj.weight"] = q_proj_weight_reshaped
        # Shape: (4, 2304, 256)
        k_weight_matrices = llm_attention_kv_einsum[i, 0].transpose(*k_transpose)
        k_proj_weight_reshaped = k_weight_matrices.reshape(
            config.text_config.num_key_value_heads * config.text_config.head_dim,
            config.text_config.hidden_size
        )
        state_dict[f"language_model.model.layers.{i}.self_attn.k_proj.weight"] = k_proj_weight_reshaped
        # llm_attention_kv_einsum[i, 1].shape = (num_key_value_heads, hidden_size, head_dim)
        v_weight_matrices = llm_attention_kv_einsum[i, 1].transpose(*v_transpose) # Shape: (4, 2304, 256)
        v_proj_weight_reshaped = v_weight_matrices.reshape(
            config.text_config.num_key_value_heads * config.text_config.head_dim,
            config.text_config.hidden_size
        )
        state_dict[f"language_model.model.layers.{i}.self_attn.v_proj.weight"] = v_proj_weight_reshaped

        # output projection.

        # llm_attention_attn_vec_einsum[i].shape = (8, 256, 2304)
        o_proj_weight_reshaped = llm_attention_attn_vec_einsum[i].transpose(*o_transpose).reshape(config.text_config.hidden_size, config.text_config.num_attention_heads * config.text_config.head_dim)
        state_dict[f"language_model.model.layers.{i}.self_attn.o_proj.weight"] = o_proj_weight_reshaped
        # mlp layers
        gate_proj_weight = llm_mlp_gating_einsum[i, 0]
        state_dict[f"language_model.model.layers.{i}.mlp.gate_proj.weight"] = gate_proj_weight.transpose()
        up_proj_weight = llm_mlp_gating_einsum[i, 1]
        state_dict[f"language_model.model.layers.{i}.mlp.up_proj.weight"] = up_proj_weight.transpose()
        state_dict[f"language_model.model.layers.{i}.mlp.down_proj.weight"] = llm_mlp_linear[i].transpose()
        state_dict[f"language_model.model.layers.{i}.input_layernorm.weight"] = llm_input_layernorm[i]
        state_dict[f"language_model.model.layers.{i}.post_attention_layernorm.weight"] = llm_post_attention_layernorm[i]
        state_dict[f"language_model.model.layers.{i}.pre_feedforward_layernorm.weight"] = llm_pre_feedforward_layernorm[i]
        state_dict[f"language_model.model.layers.{i}.post_feedforward_layernorm.weight"] = llm_post_feedforward_layernorm[i]
    state_dict["language_model.model.norm.weight"] = state_dict.pop("llm/final_norm/scale")
    state_dict["language_model.lm_head.weight"] = embedding_vector # weights are tied.
    [k for k in state_dict if not k.startswith('vision') and not k.startswith('language')]
    # fmt: on
    for key, value in state_dict.items():
        if not isinstance(value, torch.Tensor):
            try:
                if value.dtype == jnp.bfloat16:
                    value = jnp.array(value).astype(jnp.float32)
                    value = np.array(value)
                    state_dict[key] = torch.from_numpy(value).to(torch.bfloat16)
                else:
                    state_dict[key] = torch.from_numpy(value)
            except Exception as initial_exception:
                raise ValueError(f"Conversion failed from jax weights with {initial_exception}. Check your inputs.")
    return state_dict